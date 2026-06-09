from rag.domain.entities.document import Document, DocumentStatus
from rag.domain.value_objects.splitter_config import SplitterConfig
from rag.domain.ports.document_repository import DocumentRepositoryPort
from rag.infra.repositories.base import BaseRepository, to_uuid, acquire_connection


class PgDocumentRepository(DocumentRepositoryPort, BaseRepository):
    """PostgreSQL 实现的文档仓储"""

    async def save(self, document: Document) -> Document:
        cfg = document.splitter_config
        row = await self._fetch_one(
            """INSERT INTO document (
                project_id, filename, storage_key, file_size, file_type,
                checksum, status, splitter_strategy,
                chunk_size, chunk_overlap, splitter_min_chars, splitter_max_chars
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            RETURNING id, project_id, filename, storage_key, file_size, file_type,
                checksum, status, splitter_strategy,
                chunk_size, chunk_overlap, splitter_min_chars, splitter_max_chars,
                chunk_count, error_message, created_at, updated_at""",
            to_uuid(document.project_id),
            document.filename,
            document.storage_key,
            document.file_size,
            document.file_type,
            document.checksum,
            document.status.value,
            cfg.strategy,
            cfg.chunk_size,
            cfg.chunk_overlap,
            cfg.min_chars,
            cfg.max_chars,
        )
        return _row_to_document(row)

    async def get_by_id(self, document_id: str) -> Document | None:
        row = await self._fetch_one(
            """SELECT id, project_id, filename, storage_key, file_size, file_type,
                checksum, status, splitter_strategy,
                chunk_size, chunk_overlap, splitter_min_chars, splitter_max_chars,
                chunk_count, error_message, created_at, updated_at
            FROM document WHERE id = $1""",
            to_uuid(document_id),
        )
        if row is None:
            return None
        return _row_to_document(row)

    async def list_by_project(self, project_id: str) -> list[Document]:
        rows = await self._fetch_all(
            """SELECT id, project_id, filename, storage_key, file_size, file_type,
                checksum, status, splitter_strategy,
                chunk_size, chunk_overlap, splitter_min_chars, splitter_max_chars,
                chunk_count, error_message, created_at, updated_at
            FROM document WHERE project_id = $1 ORDER BY created_at DESC""",
            to_uuid(project_id),
        )
        return [_row_to_document(row) for row in rows]

    async def update_status(self, document_id: str, status: DocumentStatus, error_message: str = "") -> None:
        async with acquire_connection() as conn:
            if error_message:
                await conn.execute(
                    "UPDATE document SET status = $1, error_message = $2, updated_at = now() WHERE id = $3",
                    status.value, error_message, to_uuid(document_id),
                )
            else:
                await conn.execute(
                    "UPDATE document SET status = $1, updated_at = now() WHERE id = $2",
                    status.value, to_uuid(document_id),
                )

    async def update_chunk_count(self, document_id: str, chunk_count: int) -> None:
        await self._execute(
            "UPDATE document SET chunk_count = $1, updated_at = now() WHERE id = $2",
            chunk_count, to_uuid(document_id),
        )

    async def get_by_storage_key(self, storage_key: str) -> Document | None:
        row = await self._fetch_one(
            """SELECT id, project_id, filename, storage_key, file_size, file_type,
                checksum, status, splitter_strategy,
                chunk_size, chunk_overlap, splitter_min_chars, splitter_max_chars,
                chunk_count, error_message, created_at, updated_at
            FROM document WHERE storage_key = $1""",
            storage_key,
        )
        if row is None:
            return None
        return _row_to_document(row)

    async def delete(self, document_id: str) -> bool:
        return await self._delete_by_id("document", document_id)


def _row_to_document(row) -> Document:
    return Document(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        filename=row["filename"],
        storage_key=row["storage_key"],
        file_size=row["file_size"],
        file_type=row["file_type"],
        checksum=row["checksum"],
        status=DocumentStatus(row["status"]),
        splitter_config=SplitterConfig(
            strategy=row["splitter_strategy"],
            chunk_size=row["chunk_size"],
            chunk_overlap=row["chunk_overlap"],
            min_chars=row["splitter_min_chars"],
            max_chars=row["splitter_max_chars"],
        ),
        chunk_count=row["chunk_count"],
        error_message=row["error_message"] or "",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
