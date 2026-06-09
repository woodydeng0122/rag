from rag.domain.entities.chunk import Chunk
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.infra.database.connection import get_pool


class PgChunkRepository(ChunkRepositoryPort):
    """PostgreSQL 实现的分块仓储"""

    async def save_batch(self, chunks: list[Chunk], document_id: str = "") -> None:
        if not chunks:
            return
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.executemany(
                """INSERT INTO chunk (id, document_id, content, index, heading, source_file)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO UPDATE SET content = $3, heading = $5""",
                [
                    (c.id, _to_uuid(document_id), c.content, c.index, c.heading, c.source_file)
                    for c in chunks
                ],
            )

    async def list_by_document(self, document_id: str) -> list[Chunk]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, document_id, content, index, heading, source_file FROM chunk WHERE document_id = $1 ORDER BY index",
                _to_uuid(document_id),
            )
        return [_row_to_chunk(row) for row in rows]

    async def list_by_project(self, project_id: str, limit: int = 20, offset: int = 0) -> list[Chunk]:
        """按项目查询分块（跨文档），支持分页"""
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT c.id, c.content, c.index, c.heading, c.source_file
                   FROM chunk c
                   JOIN document d ON c.document_id = d.id
                   WHERE d.project_id = $1
                   ORDER BY c.created_at DESC
                   LIMIT $2 OFFSET $3""",
                _to_uuid(project_id),
                limit,
                offset,
            )
        return [_row_to_chunk(row) for row in rows]

    async def search_by_project(self, project_id: str, query: str, limit: int = 20, offset: int = 0) -> list[Chunk]:
        """按项目搜索分块内容，支持分页"""
        pool = get_pool()
        async with pool.acquire() as conn:
            if query:
                rows = await conn.fetch(
                    """SELECT c.id, c.content, c.index, c.heading, c.source_file
                       FROM chunk c
                       JOIN document d ON c.document_id = d.id
                       WHERE d.project_id = $1 AND c.content ILIKE $2
                       ORDER BY c.created_at DESC
                       LIMIT $3 OFFSET $4""",
                    _to_uuid(project_id),
                    f"%{query}%",
                    limit,
                    offset,
                )
            else:
                rows = await conn.fetch(
                    """SELECT c.id, c.content, c.index, c.heading, c.source_file
                       FROM chunk c
                       JOIN document d ON c.document_id = d.id
                       WHERE d.project_id = $1
                       ORDER BY c.created_at DESC
                       LIMIT $2 OFFSET $3""",
                    _to_uuid(project_id),
                    limit,
                    offset,
                )
        return [_row_to_chunk(row) for row in rows]

    async def get_by_ids(self, chunk_ids: list[str]) -> list[Chunk]:
        """按 ID 列表批量查询 chunk"""
        if not chunk_ids:
            return []
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT id, content, index, heading, source_file
                   FROM chunk WHERE id = ANY($1::varchar[])""",
                chunk_ids,
            )
        return [_row_to_chunk(row) for row in rows]


def _to_uuid(value: str) -> str:
    return value


def _row_to_chunk(row) -> Chunk:
    return Chunk(
        id=row["id"],
        content=row["content"],
        index=row["index"],
        source_file=row["source_file"],
        heading=row["heading"],
    )
