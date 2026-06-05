import json
import os
from pathlib import Path
from rag.domain.entities.embedding import Embedding
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort


class JsonlEmbeddingRepository(EmbeddingRepositoryPort):
    """JSONL 文件实现的嵌入仓储"""

    def save(self, embeddings: list[Embedding], filepath: str) -> None:
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            for emb in embeddings:
                f.write(json.dumps({
                    "id": emb.chunk_id,
                    "embedding": emb.vector,
                }, ensure_ascii=False) + '\n')

    def load(self, filepath: str) -> list[Embedding]:
        embeddings = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                embeddings.append(Embedding(
                    chunk_id=data["id"],
                    vector=data["embedding"],
                ))
        return embeddings

    async def save_batch(self, embeddings: list[Embedding], embedder_model: str = "") -> None:
        raise NotImplementedError("JSONL 仓储不支持 save_batch，请使用 PG 仓储")

    async def get_by_chunk_id(self, chunk_id: str) -> Embedding | None:
        raise NotImplementedError("JSONL 仓储不支持 get_by_chunk_id，请使用 PG 仓储")
