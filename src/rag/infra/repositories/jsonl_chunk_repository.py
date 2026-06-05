import json
from pathlib import Path
from rag.domain.entities.chunk import Chunk
from rag.domain.ports.chunk_repository import ChunkRepositoryPort


class JsonlChunkRepository(ChunkRepositoryPort):
    """JSONL 文件实现的分块仓储"""

    def save(self, chunks: list[Chunk], filepath: str) -> None:
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps({
                    "id": chunk.id,
                    "content": chunk.content,
                    "index": chunk.index,
                    "source_file": chunk.source_file,
                    "heading": chunk.heading,
                }, ensure_ascii=False) + '\n')
        print(f"分块结果已保存: {output_path}")

    def load(self, filepath: str) -> list[Chunk]:
        chunks = []
        if not Path(filepath).exists():
            return chunks
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                chunks.append(Chunk(
                    id=data["id"],
                    content=data["content"],
                    index=data.get("index", 0),
                    source_file=data.get("source_file", ""),
                    heading=data.get("heading", ""),
                ))
        return chunks

    async def save_batch(self, chunks: list[Chunk], document_id: str = "") -> None:
        raise NotImplementedError("JSONL 仓储不支持 save_batch，请使用 PG 仓储")

    async def list_by_document(self, document_id: str) -> list[Chunk]:
        raise NotImplementedError("JSONL 仓储不支持 list_by_document，请使用 PG 仓储")
