import asyncio
import logging

from rag.application.task_manager import TaskManager
from rag.application.usecases.generation_task_runner import GenerationTaskRunner
from rag.domain.entities.chunk import Chunk
from rag.domain.value_objects.generate_config import GenerateConfig
from rag.domain.entities.generation_task import GenerationTask, TaskStatus
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.generation_task_repository import GenerationTaskRepositoryPort
from rag.domain.ports.golden_dataset_repository import GoldenDatasetRepositoryPort
from rag.domain.ports.llm import LLMPort

logger = logging.getLogger(__name__)


class GenerateGoldenUseCase:
    """LLM 驱动的黄金数据集生成用例 — 仅负责编排，生成逻辑委托给 GenerationTaskRunner"""

    def __init__(
        self,
        llm: LLMPort,
        golden_repo: GoldenDatasetRepositoryPort,
        chunk_repo: ChunkRepositoryPort,
        task_repo: GenerationTaskRepositoryPort,
    ):
        self.llm = llm
        self.golden_repo = golden_repo
        self.chunk_repo = chunk_repo
        self.task_repo = task_repo

    async def submit_with_runner(
        self,
        project_id: str,
        document_ids: list[str] | None = None,
        chunk_ids: list[str] | None = None,
        config: GenerateConfig | None = None,
        task_manager: TaskManager | None = None,
    ) -> GenerationTask:
        """创建生成任务，使用 GenerationTaskRunner 支持事件流，并注册到 TaskManager"""
        if config is None:
            config = GenerateConfig()

        # 加载目标 chunks
        chunks_by_doc = await self._load_chunks_by_doc(project_id, document_ids, chunk_ids)

        total_chunks = sum(len(v) for v in chunks_by_doc.values())
        estimated_total = config.estimate_total(total_chunks)

        # 创建任务
        task = GenerationTask(
            project_id=project_id,
            status=TaskStatus.RUNNING,
            total=estimated_total,
            document_ids=document_ids or [],
            chunk_ids=chunk_ids or [],
            config=config,
        )
        task = await self.task_repo.save(task)

        # 创建 Runner
        runner = GenerationTaskRunner(
            llm=self.llm,
            golden_repo=self.golden_repo,
            chunk_repo=self.chunk_repo,
            task_repo=self.task_repo,
        )

        # 注册到 TaskManager
        if task_manager is not None:
            task_manager.register(task.id, runner)

        # 启动后台协程
        async def _run_and_cleanup():
            try:
                async for _ in runner.run(task, project_id, chunks_by_doc, config):
                    pass
            finally:
                if task_manager is not None:
                    task_manager.remove(task.id)

        asyncio.create_task(_run_and_cleanup())

        return task

    async def _load_chunks_by_doc(
        self,
        project_id: str,
        document_ids: list[str] | None,
        chunk_ids: list[str] | None,
    ) -> dict[str, list[Chunk]]:
        """按文档分组加载目标 chunks"""
        chunks_by_doc: dict[str, list[Chunk]] = {}
        if chunk_ids:
            all_chunks = await self.chunk_repo.list_by_project(project_id, limit=10000, offset=0)
            selected = {c for c in all_chunks if c.id in set(chunk_ids)}
            for c in selected:
                chunks_by_doc.setdefault(c.source_file, []).append(c)
        elif document_ids:
            for doc_id in document_ids:
                doc_chunks = await self.chunk_repo.list_by_document(doc_id)
                chunks_by_doc[doc_id] = doc_chunks
        else:
            raise ValueError("必须提供 document_ids 或 chunk_ids")
        return chunks_by_doc
