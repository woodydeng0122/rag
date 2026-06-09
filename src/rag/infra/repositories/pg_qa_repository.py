import json

from rag.domain.entities.qa import QASession, QAMessage, QAMessageChunk
from rag.domain.ports.qa_repository import QARepositoryPort
from rag.infra.repositories.base import BaseRepository, to_uuid


_SESSION_COLS = "id, project_id, title, created_at, updated_at"
_MESSAGE_COLS = "id, session_id, role, content, chunks, latency_ms, created_at"


class PgQARepository(QARepositoryPort, BaseRepository):
    """PostgreSQL 实现的问答仓储"""

    async def create_session(self, project_id: str, title: str) -> QASession:
        row = await self._fetch_one(
            f"""INSERT INTO qa_session (project_id, title)
                VALUES ($1, $2)
                RETURNING {_SESSION_COLS}""",
            to_uuid(project_id),
            title,
        )
        return _row_to_session(row)

    async def list_sessions(self, project_id: str) -> list[QASession]:
        rows = await self._fetch_all(
            f"SELECT {_SESSION_COLS} FROM qa_session WHERE project_id = $1 ORDER BY updated_at DESC",
            to_uuid(project_id),
        )
        return [_row_to_session(r) for r in rows]

    async def get_session(self, session_id: str) -> QASession | None:
        row = await self._fetch_one(
            f"SELECT {_SESSION_COLS} FROM qa_session WHERE id = $1",
            to_uuid(session_id),
        )
        return _row_to_session(row) if row else None

    async def update_session_title(self, session_id: str, title: str) -> None:
        await self._execute(
            "UPDATE qa_session SET title = $1, updated_at = now() WHERE id = $2",
            title,
            to_uuid(session_id),
        )

    async def delete_session(self, session_id: str) -> bool:
        return await self._delete_by_id("qa_session", session_id)

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        chunks: list[dict] | None = None,
        latency_ms: int | None = None,
    ) -> QAMessage:
        row = await self._fetch_one(
            f"""INSERT INTO qa_message (session_id, role, content, chunks, latency_ms)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING {_MESSAGE_COLS}""",
            to_uuid(session_id),
            role,
            content,
            json.dumps(chunks or [], ensure_ascii=False),
            latency_ms,
        )
        # 插入消息时更新 session 的 updated_at
        await self._execute(
            "UPDATE qa_session SET updated_at = now() WHERE id = $1",
            to_uuid(session_id),
        )
        return _row_to_message(row)

    async def list_messages(self, session_id: str) -> list[QAMessage]:
        rows = await self._fetch_all(
            f"SELECT {_MESSAGE_COLS} FROM qa_message WHERE session_id = $1 ORDER BY created_at ASC",
            to_uuid(session_id),
        )
        return [_row_to_message(r) for r in rows]


def _row_to_session(row) -> QASession:
    return QASession(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        title=row["title"] or "",
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _row_to_message(row) -> QAMessage:
    chunks_raw = row["chunks"]
    if isinstance(chunks_raw, str):
        chunks_data = json.loads(chunks_raw)
    elif isinstance(chunks_raw, list):
        chunks_data = chunks_raw
    else:
        chunks_data = []

    chunks = [
        QAMessageChunk(
            chunk_id=c.get("chunk_id", ""),
            content=c.get("content", ""),
            score=c.get("score", 0.0),
            source_file=c.get("source_file", ""),
            heading=c.get("heading", ""),
        )
        for c in chunks_data
    ]

    return QAMessage(
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        role=row["role"],
        content=row["content"],
        chunks=chunks,
        latency_ms=row.get("latency_ms"),
        created_at=str(row["created_at"]),
    )
