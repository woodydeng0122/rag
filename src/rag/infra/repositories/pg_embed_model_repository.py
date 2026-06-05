from datetime import datetime

from rag.domain.entities.embed_model import EmbedModel
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.infra.database.connection import get_pool


class PgEmbedModelRepository(EmbedModelRepositoryPort):
    """PostgreSQL 实现的嵌入模型仓储"""

    async def save(self, model: EmbedModel) -> EmbedModel:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO embed_model (name, dimension, description, status)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (name) DO UPDATE SET dimension = $2, description = $3, status = $4, updated_at = now()
                RETURNING id, name, dimension, description, status, created_at, updated_at""",
                model.name, model.dimension, model.description, model.status,
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
                    """INSERT INTO embed_model (name, dimension, description, status)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (name) DO UPDATE SET dimension = $2, description = $3, status = $4, updated_at = now()
                    RETURNING id, name, dimension, description, status, created_at, updated_at""",
                    m.name, m.dimension, m.description, m.status,
                )
                results.append(_row_to_model(row))
        return results

    async def get_all(self) -> list[EmbedModel]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, name, dimension, description, status, created_at, updated_at FROM embed_model ORDER BY name"
            )
        return [_row_to_model(r) for r in rows]

    async def get_by_id(self, model_id: str) -> EmbedModel | None:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, dimension, description, status, created_at, updated_at FROM embed_model WHERE id = $1",
                model_id,
            )
        if row is None:
            return None
        return _row_to_model(row)

    async def get_by_name(self, name: str) -> EmbedModel | None:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, dimension, description, status, created_at, updated_at FROM embed_model WHERE name = $1",
                name,
            )
        if row is None:
            return None
        return _row_to_model(row)

    async def update_status(self, model_id: str, status: str) -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE embed_model SET status = $1, updated_at = now() WHERE id = $2",
                status, model_id,
            )


def _row_to_model(row) -> EmbedModel:
    return EmbedModel(
        id=str(row["id"]),
        name=row["name"],
        dimension=row["dimension"],
        description=row["description"] or "",
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
