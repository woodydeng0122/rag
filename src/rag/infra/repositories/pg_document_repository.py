from rag.domain.entities.document import Document
from rag.domain.ports.document_repository import DocumentRepositoryPort
from rag.infra.database.connection import get_pool


class PgDocumentRepository(DocumentRepositoryPort):
    """PostgreSQL 实现的文档仓储"""

    async def save(self, document: Document) -> Document:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO document (
                    project_id, filename, file_path, file_size, file_type,
                    checksum, status, splitter_strategy,
                    chunk_size, chunk_overlap, splitter_min_chars, splitter_max_chars
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                RETURNING id, project_id, filename, file_path, file_size, file_type,
                    checksum, status, splitter_strategy,
                    chunk_size, chunk_overlap, splitter_min_chars, splitter_max_chars,
                    chunk_count, error_message, created_at, updated_at""",
                _to_uuid(document.project_id),
                document.filename,
                document.file_path,
                document.file_size,
                document.file_type,
                document.checksum,
                document.status,
                document.splitter_strategy,
                document.chunk_size,
                document.chunk_overlap,
                document.splitter_min_chars,
                document.splitter_max_chars,
            )
        return _row_to_document(row)

    async def get_by_id(self, document_id: str) -> Document | None:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT id, project_id, filename, file_path, file_size, file_type,
                    checksum, status, splitter_strategy,
                    chunk_size, chunk_overlap, splitter_min_chars, splitter_max_chars,
                    chunk_count, error_message, created_at, updated_at
                FROM document WHERE id = $1""",
                _to_uuid(document_id),
            )
        if row is None:
            return None
        return _row_to_document(row)

    async def list_by_project(self, project_id: str) -> list[Document]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT id, project_id, filename, file_path, file_size, file_type,
                    checksum, status, splitter_strategy,
                    chunk_size, chunk_overlap, splitter_min_chars, splitter_max_chars,
                    chunk_count, error_message, created_at, updated_at
                FROM document WHERE project_id = $1 ORDER BY created_at DESC""",
                _to_uuid(project_id),
            )
        return [_row_to_document(row) for row in rows]

    async def update_status(self, document_id: str, status: str, error_message: str = "") -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            if error_message:
                await conn.execute(
                    "UPDATE document SET status = $1, error_message = $2, updated_at = now() WHERE id = $3",
                    status, error_message, _to_uuid(document_id),
                )
            else:
                await conn.execute(
                    "UPDATE document SET status = $1, updated_at = now() WHERE id = $2",
                    status, _to_uuid(document_id),
                )

    async def update_chunk_count(self, document_id: str, chunk_count: int) -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE document SET chunk_count = $1, updated_at = now() WHERE id = $2",
                chunk_count, _to_uuid(document_id),
            )

    async def delete(self, document_id: str) -> bool:
        pool = get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM document WHERE id = $1",
                _to_uuid(document_id),
            )
            return result == "DELETE 1"


def _to_uuid(value: str) -> str:
    return value


def _row_to_document(row) -> Document:
    return Document(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        filename=row["filename"],
        file_path=row["file_path"],
        file_size=row["file_size"],
        file_type=row["file_type"],
        checksum=row["checksum"],
        status=row["status"],
        splitter_strategy=row["splitter_strategy"],
        chunk_size=row["chunk_size"],
        chunk_overlap=row["chunk_overlap"],
        splitter_min_chars=row["splitter_min_chars"],
        splitter_max_chars=row["splitter_max_chars"],
        chunk_count=row["chunk_count"],
        error_message=row["error_message"] or "",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
