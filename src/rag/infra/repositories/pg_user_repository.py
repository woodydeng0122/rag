from rag.domain.entities.user import User
from rag.domain.ports.user_repository import UserRepositoryPort
from rag.infra.repositories.base import BaseRepository, to_uuid


class PgUserRepository(UserRepositoryPort, BaseRepository):
    """PostgreSQL 实现的用户仓储"""

    _SELECT = """SELECT id, username, password_hash, created_at FROM "user\""""

    async def get_by_id(self, user_id: str) -> User | None:
        row = await self._fetch_one(
            f'{self._SELECT} WHERE id = $1',
            to_uuid(user_id),
        )
        if row is None:
            return None
        return _row_to_user(row)

    async def get_by_username(self, username: str) -> User | None:
        row = await self._fetch_one(
            f'{self._SELECT} WHERE username = $1',
            username,
        )
        if row is None:
            return None
        return _row_to_user(row)

    async def list_all(self) -> list[User]:
        rows = await self._fetch_all(
            f"{self._SELECT} ORDER BY created_at ASC"
        )
        return [_row_to_user(row) for row in rows]

    async def create(self, username: str, password_hash: str) -> User:
        row = await self._fetch_one(
            """INSERT INTO "user" (username, password_hash)
            VALUES ($1, $2)
            RETURNING id, username, password_hash, created_at""",
            username,
            password_hash,
        )
        return _row_to_user(row)

    async def update_password(self, user_id: str, password_hash: str) -> User:
        row = await self._fetch_one(
            """UPDATE "user" SET password_hash = $1
            WHERE id = $2
            RETURNING id, username, password_hash, created_at""",
            password_hash,
            to_uuid(user_id),
        )
        if row is None:
            raise ValueError(f"用户 {user_id} 不存在")
        return _row_to_user(row)

    async def delete(self, user_id: str) -> bool:
        return await self._delete_by_id("user", user_id)


def _row_to_user(row) -> User:
    return User(
        id=str(row["id"]),
        username=row["username"],
        password_hash=row["password_hash"],
        created_at=row["created_at"],
    )
