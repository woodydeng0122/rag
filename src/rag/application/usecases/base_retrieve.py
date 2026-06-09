from rag.domain.ports.retriever import RetrieverPort
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.application.results.retrieve_result import RetrievedChunk


class BaseRetrieveUseCase:
    """检索基类 — 封装"检索 → 加载分块 → 匹配"的共享逻辑

    子类只需关注自身特有的编排（如 LLM 生成）。
    """

    def __init__(
        self,
        retriever: RetrieverPort,
        chunk_repo: ChunkRepositoryPort,
    ):
        self.retriever = retriever
        self.chunk_repo = chunk_repo

    async def _retrieve_chunks(self, query: str, project_id: str, top_k: int = 3) -> list[RetrievedChunk]:
        """检索并加载分块内容 — 共享逻辑"""
        output = await self.retriever.retrieve(query, project_id=project_id, top_k=top_k)
        chunk_ids = [r.chunk_id for r in output.results]
        chunks = await self.chunk_repo.get_by_ids(chunk_ids)
        chunk_map = {c.id: c for c in chunks}

        retrieved = []
        for r in output.results:
            chunk = chunk_map.get(r.chunk_id)
            if chunk:
                retrieved.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        content=chunk.content,
                        source_file=chunk.source_file,
                        heading=chunk.heading,
                        score=r.score,
                    )
                )
        return retrieved
