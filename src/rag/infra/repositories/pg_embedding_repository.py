from rag.domain.entities.embedding import Embedding
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort
from rag.infra.database.connection import get_pool


class PgEmbeddingRepository(EmbeddingRepositoryPort):
    """PostgreSQL + pgvector 实现的嵌入仓储"""

    def save(self, embeddings: list[Embedding], filepath: str) -> None:
        raise NotImplementedError("PG 仓储不支持 JSONL save，请使用 save_batch")

    def load(self, filepath: str) -> list[Embedding]:
        raise NotImplementedError("PG 仓储不支持 JSONL load，请使用数据库查询")

    async def save_batch(self, embeddings: list[Embedding], embedder_model: str = "") -> None:
        if not embeddings:
            return
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.executemany(
                """INSERT INTO embedding (chunk_id, vector, embedder_model)
                VALUES ($1, $2::vector, $3)
                ON CONFLICT (chunk_id) DO UPDATE SET vector = $2::vector, embedder_model = $3""",
                [
                    (e.chunk_id, _vector_to_str(e.vector), embedder_model)
                    for e in embeddings
                ],
            )


def _vector_to_str(vector: list[float]) -> str:
    """将向量列表转换为 pgvector 接受的字符串格式"""
    return "[" + ",".join(str(v) for v in vector) + "]"
