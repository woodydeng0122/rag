from abc import ABC, abstractmethod

from rag.domain.entities.qa import QASession, QAMessage


class QARepositoryPort(ABC):
    """问答仓储端口 — 会话与消息的持久化抽象"""

    @abstractmethod
    async def create_session(self, project_id: str, title: str) -> QASession: ...

    @abstractmethod
    async def list_sessions(self, project_id: str) -> list[QASession]: ...

    @abstractmethod
    async def get_session(self, session_id: str) -> QASession | None: ...

    @abstractmethod
    async def update_session_title(self, session_id: str, title: str) -> None: ...

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool: ...

    @abstractmethod
    async def add_message(self, session_id: str, role: str, content: str, chunks: list[dict] | None = None, latency_ms: int | None = None) -> QAMessage: ...

    @abstractmethod
    async def list_messages(self, session_id: str) -> list[QAMessage]: ...

    @abstractmethod
    async def count_today_queries(self, project_id: str) -> int: ...
