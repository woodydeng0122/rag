import json

from rag.domain.entities.embed_model import EmbedModel, ModelStatus
from rag.domain.value_objects.model_config import ModelConfig
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.infra.repositories.base import BaseRepository, acquire_connection


class PgEmbedModelRepository(EmbedModelRepositoryPort, BaseRepository):
    """PostgreSQL 实现的嵌入模型仓储"""

    _UPSERT_SQL = """INSERT INTO embed_model (name, model_type, dimension, description, status, metadata)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                ON CONFLICT (name) DO UPDATE SET
                    model_type = $2, dimension = $3, description = $4, status = $5, metadata = $6::jsonb, updated_at = now()
                RETURNING id, name, model_type, dimension, description, status, metadata, created_at, updated_at"""

    _SELECT_ALL = "SELECT id, name, model_type, dimension, description, status, metadata, created_at, updated_at FROM embed_model"

    async def save(self, model: EmbedModel) -> EmbedModel:
        row = await self._fetch_one(
            self._UPSERT_SQL,
            model.name, model.model_type, model.dimension, model.description, model.status.value,
            json.dumps(model.config.to_dict(), ensure_ascii=False),
        )
        return _row_to_model(row)

    async def save_batch(self, models: list[EmbedModel]) -> list[EmbedModel]:
        if not models:
            return []
        results = []
        async with acquire_connection() as conn:
            for m in models:
                row = await conn.fetchrow(
                    self._UPSERT_SQL,
                    m.name, m.model_type, m.dimension, m.description, m.status.value,
                    json.dumps(m.config.to_dict(), ensure_ascii=False),
                )
                results.append(_row_to_model(row))
        return results

    async def get_all(self) -> list[EmbedModel]:
        rows = await self._fetch_all(
            f"{self._SELECT_ALL} ORDER BY name"
        )
        return [_row_to_model(r) for r in rows]

    async def get_by_id(self, model_id: str) -> EmbedModel | None:
        row = await self._fetch_one(
            f"{self._SELECT_ALL} WHERE id = $1",
            model_id,
        )
        if row is None:
            return None
        return _row_to_model(row)

    async def get_by_name(self, name: str) -> EmbedModel | None:
        row = await self._fetch_one(
            f"{self._SELECT_ALL} WHERE name = $1",
            name,
        )
        if row is None:
            return None
        return _row_to_model(row)

    async def update(self, model: EmbedModel) -> EmbedModel:
        row = await self._fetch_one(
            """UPDATE embed_model SET name = $1, description = $2, status = $3, updated_at = now()
            WHERE id = $4
            RETURNING id, name, model_type, dimension, description, status, metadata, created_at, updated_at""",
            model.name, model.description, model.status.value, model.id,
        )
        if row is None:
            raise ValueError(f"嵌入模型 {model.id} 不存在")
        return _row_to_model(row)

    async def delete(self, model_id: str) -> bool:
        return await self._delete_by_id("embed_model", model_id)


def _row_to_model(row) -> EmbedModel:
    config = row["metadata"]
    if isinstance(config, str):
        config = json.loads(config)
    return EmbedModel.reconstruct(
        id=str(row["id"]),
        name=row["name"],
        model_type=row["model_type"],
        dimension=row["dimension"],
        description=row["description"] or "",
        status=ModelStatus(row["status"]),
        config=ModelConfig.from_dict(config),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
