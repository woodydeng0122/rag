from rag.domain.entities.embedding import Embedding
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.infra.database.connection import get_pool


class PgEmbeddingRepository(EmbeddingRepositoryPort):
    """PostgreSQL + pgvector 实现的嵌入仓储"""

    async def save_batch(self, embeddings: list[Embedding]) -> None:
        if not embeddings:
            return
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.executemany(
                """INSERT INTO embedding (chunk_id, vector, embedder_model)
                VALUES ($1, $2::vector, $3)
                ON CONFLICT (chunk_id) DO UPDATE SET vector = $2::vector, embedder_model = $3""",
                [
                    (e.chunk_id, _vector_to_str(e.vector), e.embedder_model)
                    for e in embeddings
                ],
            )

    async def get_by_chunk_id(self, chunk_id: str) -> Embedding | None:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT chunk_id, vector, embedder_model FROM embedding WHERE chunk_id = $1",
                chunk_id,
            )
        if row is None:
            return None
        vector_str = row["vector"]
        vector = [float(v) for v in vector_str.strip("[]").split(",")]
        return Embedding(chunk_id=row["chunk_id"], vector=vector, embedder_model=row.get("embedder_model", ""))

    async def list_by_project(self, project_id: str) -> list[Embedding]:
        """按项目查询所有嵌入向量"""
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT e.chunk_id, e.vector, e.embedder_model
                   FROM embedding e
                   JOIN chunk c ON e.chunk_id = c.id
                   JOIN document d ON c.document_id = d.id
                   WHERE d.project_id = $1""",
                project_id,
            )
        return [_row_to_embedding(row) for row in rows]


def _vector_to_str(vector: list[float]) -> str:
    """将向量列表转换为 pgvector 接受的字符串格式"""
    return "[" + ",".join(str(v) for v in vector) + "]"


def _row_to_embedding(row) -> Embedding:
    vector_str = row["vector"]
    vector = [float(v) for v in vector_str.strip("[]").split(",")]
    return Embedding(chunk_id=row["chunk_id"], vector=vector, embedder_model=row.get("embedder_model", ""))
