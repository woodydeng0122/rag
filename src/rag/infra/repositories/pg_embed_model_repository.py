import json

from rag.domain.entities.embed_model import EmbedModel, ModelStatus
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.infra.database.connection import get_pool


class PgEmbedModelRepository(EmbedModelRepositoryPort):
    """PostgreSQL 实现的嵌入模型仓储"""

    async def save(self, model: EmbedModel) -> EmbedModel:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO embed_model (name, dimension, description, status, metadata)
                VALUES ($1, $2, $3, $4, $5::jsonb)
                ON CONFLICT (name) DO UPDATE SET
                    dimension = $2, description = $3, status = $4, metadata = $5::jsonb, updated_at = now()
                RETURNING id, name, dimension, description, status, metadata, created_at, updated_at""",
                model.name, model.dimension, model.description, model.status.value,
                json.dumps(model.config, ensure_ascii=False),
            )
        return _row_to_model(row)

    async def save_batch(self, models: list[EmbedModel]) -> list[EmbedModel]:
        if not models:
            return []
        pool = get_pool()
        results = []
        async with pool.acquire() as conn:
            for m in models:
                row = await conn.fetchrow(
                    """INSERT INTO embed_model (name, dimension, description, status, metadata)
                    VALUES ($1, $2, $3, $4, $5::jsonb)
                    ON CONFLICT (name) DO UPDATE SET
                        dimension = $2, description = $3, status = $4, metadata = $5::jsonb, updated_at = now()
                    RETURNING id, name, dimension, description, status, metadata, created_at, updated_at""",
                    m.name, m.dimension, m.description, m.status.value,
                    json.dumps(m.config, ensure_ascii=False),
                )
                results.append(_row_to_model(row))
        return results

    async def get_all(self) -> list[EmbedModel]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, name, dimension, description, status, metadata, created_at, updated_at FROM embed_model ORDER BY name"
            )
        return [_row_to_model(r) for r in rows]

    async def get_by_id(self, model_id: str) -> EmbedModel | None:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, dimension, description, status, metadata, created_at, updated_at FROM embed_model WHERE id = $1",
                model_id,
            )
        if row is None:
            return None
        return _row_to_model(row)

    async def get_by_name(self, name: str) -> EmbedModel | None:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, dimension, description, status, metadata, created_at, updated_at FROM embed_model WHERE name = $1",
                name,
            )
        if row is None:
            return None
        return _row_to_model(row)

    async def update_status(self, model_id: str, status: ModelStatus) -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE embed_model SET status = $1, updated_at = now() WHERE id = $2",
                status.value, model_id,
            )

    async def update(self, model: EmbedModel) -> EmbedModel:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE embed_model SET name = $1, description = $2, updated_at = now()
                WHERE id = $3
                RETURNING id, name, dimension, description, status, metadata, created_at, updated_at""",
                model.name, model.description, model.id,
            )
        if row is None:
            raise ValueError(f"嵌入模型 {model.id} 不存在")
        return _row_to_model(row)

    async def delete(self, model_id: str) -> bool:
        pool = get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM embed_model WHERE id = $1",
                model_id,
            )
            return result == "DELETE 1"


def _row_to_model(row) -> EmbedModel:
    config = row["metadata"]
    if isinstance(config, str):
        import json as _json
        config = _json.loads(config)
    return EmbedModel(
        id=str(row["id"]),
        name=row["name"],
        dimension=row["dimension"],
        description=row["description"] or "",
        status=ModelStatus(row["status"]),
        config=config or {},
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
