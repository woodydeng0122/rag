from rag.application.usecases.base_retrieve import BaseRetrieveUseCase
from rag.application.results.retrieve_result import RetrieveResult


class RetrieveUseCase(BaseRetrieveUseCase):
    """检索用例 — 查询 → 检索 → 加载分块内容

    只依赖端口接口，不知道具体实现。
    """

    async def execute(self, query: str, project_id: str, top_k: int = 3) -> RetrieveResult:
        retrieved = await self._retrieve_chunks(query, project_id, top_k)
        return RetrieveResult(chunks=retrieved)
