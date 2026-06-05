from rag.domain.entities.chunk import Chunk
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.infra.database.connection import get_pool


class PgChunkRepository(ChunkRepositoryPort):
    """PostgreSQL 实现的分块仓储"""

    def save(self, chunks: list[Chunk], filepath: str) -> None:
        raise NotImplementedError("PG 仓储不支持 JSONL save，请使用 save_batch")

    def load(self, filepath: str) -> list[Chunk]:
        raise NotImplementedError("PG 仓储不支持 JSONL load，请使用 list_by_document")

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
        return [
            Chunk(
                id=row["id"],
                content=row["content"],
                index=row["index"],
                source_file=row["source_file"],
                heading=row["heading"],
            )
            for row in rows
        ]


def _to_uuid(value: str) -> str:
    return value
