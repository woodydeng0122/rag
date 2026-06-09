import time
from collections.abc import AsyncGenerator

from rag.domain.ports.retriever import RetrieverPort
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.llm import LLMPort
from rag.domain.ports.qa_repository import QARepositoryPort
from rag.application.usecases.base_retrieve import BaseRetrieveUseCase
from rag.application.results.qa_result import (
    QASessionResult,
    QAMessageResult,
    QAMessageChunkResult,
    AskStreamEvent,
)


class QAUseCase(BaseRetrieveUseCase):
    """问答用例 — 会话管理 + 检索 + LLM 流式生成

    只依赖端口接口，不知道具体实现。
    """

    def __init__(
        self,
        retriever: RetrieverPort,
        chunk_repo: ChunkRepositoryPort,
        llm: LLMPort,
        qa_repo: QARepositoryPort,
    ):
        super().__init__(retriever, chunk_repo)
        self.llm = llm
        self.qa_repo = qa_repo

    # ── 会话管理 ──

    async def create_session(self, project_id: str, title: str = "") -> QASessionResult:
        session = await self.qa_repo.create_session(project_id, title)
        return _session_to_result(session)

    async def list_sessions(self, project_id: str) -> list[QASessionResult]:
        sessions = await self.qa_repo.list_sessions(project_id)
        return [_session_to_result(s) for s in sessions]

    async def get_session(self, session_id: str) -> QASessionResult | None:
        session = await self.qa_repo.get_session(session_id)
        return _session_to_result(session) if session else None

    async def delete_session(self, session_id: str) -> bool:
        return await self.qa_repo.delete_session(session_id)

    async def get_messages(self, session_id: str) -> list[QAMessageResult]:
        messages = await self.qa_repo.list_messages(session_id)
        return [_message_to_result(m) for m in messages]

    # ── 问答（流式） ──

    async def ask_stream(
        self,
        session_id: str,
        query: str,
        project_id: str,
        top_k: int = 3,
    ) -> AsyncGenerator[AskStreamEvent, None]:
        """流式问答：检索 → 保存用户消息 → 流式生成 → 保存助手消息"""

        # 1. 保存用户消息
        await self.qa_repo.add_message(session_id, role="user", content=query)

        # 2. 如果会话无标题，用第一条问题设置标题
        session = await self.qa_repo.get_session(session_id)
        if session and not session.title:
            await self.qa_repo.update_session_title(session_id, query[:50])

        # 3. 检索
        start = time.perf_counter()
        retrieved = await self._retrieve_chunks(query, project_id, top_k)
        chunk_results = [
            QAMessageChunkResult(
                chunk_id=c.chunk_id,
                content=c.content,
                score=c.score,
                source_file=c.source_file,
                heading=c.heading,
            )
            for c in retrieved
        ]

        # 4. 发送引用来源事件
        yield AskStreamEvent(type="sources", chunks=chunk_results)

        # 5. 构建 Prompt 并流式生成
        contexts = [c.content for c in retrieved]
        prompt = self._build_prompt(contexts, query)

        full_answer = ""
        async for token in self.llm.astream(prompt):
            full_answer += token
            yield AskStreamEvent(type="chunk", data=token)

        # 6. 保存助手消息
        latency_ms = int((time.perf_counter() - start) * 1000)
        chunks_data = [
            {
                "chunk_id": c.chunk_id,
                "content": c.content,
                "score": c.score,
                "source_file": c.source_file,
                "heading": c.heading,
            }
            for c in chunk_results
        ]
        await self.qa_repo.add_message(
            session_id,
            role="assistant",
            content=full_answer,
            chunks=chunks_data,
            latency_ms=latency_ms,
        )

        # 7. 发送完成事件
        yield AskStreamEvent(type="done", latency_ms=latency_ms)

    # ── 问答（非流式，兼容旧接口） ──

    async def execute(self, query: str, project_id: str, top_k: int = 3):
        """非流式问答 — 兼容旧 /ask 接口"""
        from rag.application.results.ask_result import AskResult, ChunkResult

        retrieved = await self._retrieve_chunks(query, project_id, top_k)
        contexts = [c.content for c in retrieved]
        chunk_results = [
            ChunkResult(chunk_id=c.chunk_id, content=c.content, score=c.score)
            for c in retrieved
        ]
        prompt = self._build_prompt(contexts, query)
        answer = await self.llm.agenerate(prompt)
        return AskResult(answer=answer, chunks=chunk_results)

    @staticmethod
    def _build_prompt(contexts: list[str], query: str) -> str:
        context = "\n".join(contexts)
        return f"""请基于以下上下文回答问题,若上下文不包含相关信息,请直接回答"不包含相关信息"，不要编造。
上下文：
{context}
问题：
{query}
答案："""


def _session_to_result(session) -> QASessionResult:
    return QASessionResult(
        id=session.id,
        project_id=session.project_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _message_to_result(message) -> QAMessageResult:
    return QAMessageResult(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        chunks=[
            QAMessageChunkResult(
                chunk_id=c.chunk_id,
                content=c.content,
                score=c.score,
                source_file=c.source_file,
                heading=c.heading,
            )
            for c in message.chunks
        ],
        latency_ms=message.latency_ms,
        created_at=message.created_at,
    )
