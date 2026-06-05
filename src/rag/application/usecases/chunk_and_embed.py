from rag.domain.entities.chunk import Chunk
from rag.domain.entities.embedding import Embedding
from rag.domain.ports.dir_loader import DirLoaderPort
from rag.domain.ports.splitter import SplitterPort
from rag.domain.ports.embedder import EmbedderPort
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.embedding_repository import EmbeddingRepositoryPort


class ChunkAndEmbedUseCase:
    """分块并嵌入用例 — 加载文档 → 分块 → 嵌入 → 保存

    只依赖端口接口，不知道具体实现。
    """

    def __init__(
        self,
        loader: DirLoaderPort,
        splitter: SplitterPort,
        embedder: EmbedderPort,
        chunk_repo: ChunkRepositoryPort,
        embedding_repo: EmbeddingRepositoryPort,
    ):
        self.loader = loader
        self.splitter = splitter
        self.embedder = embedder
        self.chunk_repo = chunk_repo
        self.embedding_repo = embedding_repo

    def execute(self, doc_dir: str, chunk_file: str, embedding_file: str) -> list[Chunk]:
        # 1. 加载文档
        docs = self.loader.load_dir_md(doc_dir)

        # 2. 分块
        all_chunks: list[Chunk] = []
        for doc in docs:
            chunks = self.splitter.split(doc["text"])
            for i, chunk in enumerate(chunks):
                chunk.source_file = doc.get("path", "")
                chunk.id = f"{doc.get('path', 'doc').replace('/', '_').replace('.md', '')}_chunk_{i}"
                chunk.index = i
            all_chunks.extend(chunks)

        # 3. 保存分块
        self.chunk_repo.save(all_chunks, chunk_file)

        # 4. 嵌入
        texts = [c.content for c in all_chunks]
        vectors = self.embedder.embed(texts)

        # 5. 保存嵌入
        embeddings = [
            Embedding(chunk_id=c.id, vector=v)
            for c, v in zip(all_chunks, vectors)
        ]
        self.embedding_repo.save(embeddings, embedding_file)

        return all_chunks
