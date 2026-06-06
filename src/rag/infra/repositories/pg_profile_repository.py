from rag.domain.entities.profile import Profile
from rag.domain.ports.profile_repository import ProfileRepositoryPort
from rag.infra.database.connection import get_pool


class PgProfileRepository(ProfileRepositoryPort):
    """PostgreSQL 实现的用户配置仓储"""

    async def get(self) -> Profile:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, active_project_id FROM profile WHERE id = 1"
            )
        if row is None:
            return Profile(id=1, active_project_id=None)
        return _row_to_profile(row)

    async def upsert(self, active_project_id: str | None) -> Profile:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO profile (id, active_project_id) VALUES (1, $1)
                ON CONFLICT (id) DO UPDATE SET active_project_id = $1, updated_at = now()
                RETURNING id, active_project_id""",
                active_project_id,
            )
        return _row_to_profile(row)


def _row_to_profile(row) -> Profile:
    return Profile(
        id=row["id"],
        active_project_id=str(row["active_project_id"]) if row["active_project_id"] else None,
    )
