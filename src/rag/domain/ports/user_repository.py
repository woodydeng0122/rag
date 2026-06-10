from abc import ABC, abstractmethod

from rag.domain.entities.user import User


class UserRepositoryPort(ABC):
    """用户仓储端口 — 用户持久化的抽象"""

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def list_all(self) -> list[User]: ...

    @abstractmethod
    async def create(self, username: str, password_hash: str) -> User: ...

    @abstractmethod
    async def update_password(self, user_id: str, password_hash: str) -> User: ...

    @abstractmethod
    async def delete(self, user_id: str) -> bool: ...
