from rag.domain.entities.profile import Profile
from rag.domain.ports.profile_repository import ProfileRepositoryPort
from rag.infra.database.connection import get_pool
from rag.infra.repositories.base import to_uuid


class PgProfileRepository(ProfileRepositoryPort):
    """PostgreSQL 实现的用户配置仓储（per-user）"""

    async def get(self, user_id: str) -> Profile:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, user_id, active_project_id FROM profile WHERE user_id = $1",
                to_uuid(user_id),
            )
        if row is None:
            # 自动创建该用户的 profile 行
            return await self.upsert(user_id, None)
        return _row_to_profile(row)

    async def upsert(self, user_id: str, active_project_id: str | None) -> Profile:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO profile (user_id, active_project_id) VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET active_project_id = $2
                RETURNING id, user_id, active_project_id""",
                to_uuid(user_id),
                to_uuid(active_project_id) if active_project_id else None,
            )
        return _row_to_profile(row)


def _row_to_profile(row) -> Profile:
    return Profile(
        id=str(row["id"]),
        user_id=str(row["user_id"]) if row["user_id"] else "",
        active_project_id=str(row["active_project_id"]) if row["active_project_id"] else None,
    )
