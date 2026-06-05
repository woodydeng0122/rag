from rag.application.usecases.base_retrieve import BaseRetrieveUseCase
from rag.application.results.retrieve_result import RetrieveResult


class RetrieveUseCase(BaseRetrieveUseCase):
    """检索用例 — 查询 → 检索 → 加载分块内容

    只依赖端口接口，不知道具体实现。
    """

    def execute(self, query: str, top_k: int = 3) -> RetrieveResult:
        retrieved = self._retrieve_chunks(query, top_k)
        return RetrieveResult(chunks=retrieved)
