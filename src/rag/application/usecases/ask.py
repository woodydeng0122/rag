from rag.domain.ports.retriever import RetrieverPort
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.llm import LLMPort
from rag.application.usecases.base_retrieve import BaseRetrieveUseCase
from rag.application.results.ask_result import AskResult, ChunkResult


class AskUseCase(BaseRetrieveUseCase):
    """提问用例 — 检索 → 构建 Prompt → LLM 生成

    只依赖端口接口，不知道具体实现。
    """

    def __init__(
        self,
        retriever: RetrieverPort,
        chunk_repo: ChunkRepositoryPort,
        llm: LLMPort,
    ):
        super().__init__(retriever, chunk_repo)
        self.llm = llm

    async def execute(self, query: str, project_id: str, top_k: int = 3) -> AskResult:
        # 1. 检索并加载分块
        retrieved = await self._retrieve_chunks(query, project_id, top_k)

        # 2. 构建上下文和分块结果
        contexts = [c.content for c in retrieved]
        chunk_results = [
            ChunkResult(chunk_id=c.chunk_id, content=c.content, score=c.score)
            for c in retrieved
        ]

        # 3. 构建 Prompt
        prompt = self._build_prompt(contexts, query)

        # 4. LLM 生成
        answer = await self.llm.agenerate(prompt)

        # 5. 返回完整结果
        return AskResult(
            answer=answer,
            chunks=chunk_results,
        )

    @staticmethod
    def _build_prompt(contexts: list[str], query: str) -> str:
        context = "\n".join(contexts)
        return f"""请基于以下上下文回答问题,若上下文不包含相关信息,请直接回答"不包含相关信息"，不要编造。
上下文：
{context}
问题：
{query}
答案："""
