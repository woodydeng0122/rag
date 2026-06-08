import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from rag.application.usecases.prompts import (
    answer_generation_prompt,
    chunk_batch_question_prompt,
    whole_doc_question_prompt,
)
from rag.domain.entities.chunk import Chunk
from rag.domain.value_objects.generate_config import GenerateConfig
from rag.domain.entities.generation_task import GenerationTask, TaskStatus
from rag.domain.entities.golden_record import GoldenRecord, GoldenStatus
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.generation_task_repository import GenerationTaskRepositoryPort
from rag.domain.ports.golden_dataset_repository import GoldenDatasetRepositoryPort
from rag.domain.ports.llm import LLMPort

logger = logging.getLogger(__name__)


class FailedItem:
    """失败项上下文，用于重试"""

    def __init__(
        self,
        question: dict,
        chunks: list[Chunk],
        project_id: str,
        phase: str,
        error: str,
    ):
        self.question = question
        self.chunks = chunks
        self.project_id = project_id
        self.phase = phase
        self.error = error


class GenerationTaskRunner:
    """事件驱动的黄金数据集生成 Runner

    通过异步生成器 yield 事件字典，供 SSE 端点消费。
    支持暂停/继续/取消控制。
    同时将事件放入队列，供 SSE 端点实时消费。
    """

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

        self.pause_event = asyncio.Event()
        self.pause_event.set()  # 默认不暂停
        self.cancel_flag = asyncio.Event()

        self.task: GenerationTask | None = None
        self.failed_items: list[FailedItem] = []
        self.event_queue: asyncio.Queue[dict | None] = asyncio.Queue()

    async def run(
        self,
        task: GenerationTask,
        project_id: str,
        chunks_by_doc: dict[str, list[Chunk]],
        config: GenerateConfig,
    ) -> AsyncGenerator[dict, None]:
        """主生成流程，yield 事件字典，同时放入队列"""
        self.task = task

        try:
            event = {
                "type": "progress",
                "completed": task.completed,
                "total": task.total,
                "failed": task.failed,
            }
            yield event
            await self.event_queue.put(event)

            for doc_id, chunks in chunks_by_doc.items():
                chunks.sort(key=lambda c: c.index)
                total_chars = sum(len(c.content) for c in chunks)

                if total_chars <= config.file_char_threshold:
                    async for event in self._process_whole_doc(
                        task, project_id, chunks, config, doc_id
                    ):
                        yield event
                        await self.event_queue.put(event)
                else:
                    async for event in self._process_chunk_batches(
                        task, project_id, chunks, config, doc_id
                    ):
                        yield event
                        await self.event_queue.put(event)

                # 每个文档处理完检查取消
                if self.cancel_flag.is_set():
                    task.cancel()
                    await self.task_repo.update(task)
                    event = {"type": "task_cancelled"}
                    yield event
                    await self.event_queue.put(event)
                    await self.event_queue.put(None)  # 哨兵，通知 SSE 关闭
                    return

            task.complete()
            await self.task_repo.update(task)
            event = {
                "type": "task_done",
                "completed": task.completed,
                "failed": task.failed,
            }
            yield event
            await self.event_queue.put(event)
            await self.event_queue.put(None)  # 哨兵

        except Exception as e:
            logger.exception("生成任务 %s 异常", task.id)
            task.fail(str(e))
            await self.task_repo.update(task)
            event = {"type": "task_failed", "error": str(e)}
            yield event
            await self.event_queue.put(event)
            await self.event_queue.put(None)  # 哨兵

    async def _process_whole_doc(
        self,
        task: GenerationTask,
        project_id: str,
        chunks: list[Chunk],
        config: GenerateConfig,
        doc_id: str,
    ) -> AsyncGenerator[dict, None]:
        """整篇文档模式"""
        full_doc = "\n\n".join(c.content for c in chunks)
        chunks_info = json.dumps(
            [{"id": c.id, "heading": c.heading, "index": c.index} for c in chunks],
            ensure_ascii=False,
        )
        type_dist = config.format_type_distribution()
        n_questions = len(chunks) * config.per_chunk

        prompt = whole_doc_question_prompt(
            full_doc=full_doc,
            chunks_info=chunks_info,
            n_questions=n_questions,
            type_dist=type_dist,
            user_persona=config.user_persona,
        )

        yield {"type": "phase_start", "phase": "question_gen", "doc_id": doc_id}

        # 流式收集 LLM 输出
        raw = ""
        async for token in self.llm.astream(prompt):
            yield {"type": "llm_token", "content": token}
            raw += token

        yield {"type": "llm_done", "raw_length": len(raw)}

        # 解析 JSON
        try:
            result = LLMPort._parse_json_output(raw)
        except ValueError:
            logger.warning("整篇文档 Phase 1 失败，跳过文档")
            task.increment_failed(n_questions)
            await self.task_repo.update(task)
            yield {
                "type": "progress",
                "completed": task.completed,
                "total": task.total,
                "failed": task.failed,
            }
            return

        questions = result.get("items", result) if isinstance(result, dict) else result
        if not isinstance(questions, list):
            logger.warning("Phase 1 返回格式异常，跳过文档")
            task.increment_failed(n_questions)
            await self.task_repo.update(task)
            yield {
                "type": "progress",
                "completed": task.completed,
                "total": task.total,
                "failed": task.failed,
            }
            return

        for idx, q in enumerate(questions):
            yield {
                "type": "question_generated",
                "index": idx,
                "query": q.get("query", ""),
                "type": q.get("type", "factual"),
                "difficulty": q.get("difficulty", "medium"),
            }

        for q in questions:
            async for event in self._process_single_question(
                task, project_id, q, chunks, config
            ):
                yield event

            # 暂停/取消检查
            if self.cancel_flag.is_set():
                return
            await self.pause_event.wait()

    async def _process_chunk_batches(
        self,
        task: GenerationTask,
        project_id: str,
        chunks: list[Chunk],
        config: GenerateConfig,
        doc_id: str,
    ) -> AsyncGenerator[dict, None]:
        """分批 chunk 模式"""
        batch_size = config.chunk_batch_size
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            async for event in self._process_single_batch(
                task, project_id, batch, config, doc_id, batch_index=i // batch_size
            ):
                yield event

            if self.cancel_flag.is_set():
                return

    async def _process_single_batch(
        self,
        task: GenerationTask,
        project_id: str,
        batch: list[Chunk],
        config: GenerateConfig,
        doc_id: str,
        batch_index: int = 0,
    ) -> AsyncGenerator[dict, None]:
        """处理单个 chunk 批次"""
        chunks_text = json.dumps(
            [{"id": c.id, "content": c.content[:800]} for c in batch],
            ensure_ascii=False,
        )
        type_dist = config.format_type_distribution()
        n_questions = len(batch) * config.per_chunk

        prompt = chunk_batch_question_prompt(
            chunks_text=chunks_text,
            n_questions=n_questions,
            type_dist=type_dist,
            user_persona=config.user_persona,
        )

        yield {
            "type": "phase_start",
            "phase": "question_gen",
            "doc_id": doc_id,
            "batch_index": batch_index,
        }

        raw = ""
        async for token in self.llm.astream(prompt):
            yield {"type": "llm_token", "content": token}
            raw += token

        yield {"type": "llm_done", "raw_length": len(raw)}

        try:
            result = LLMPort._parse_json_output(raw)
        except ValueError:
            logger.warning("批次 Phase 1 失败，跳过")
            task.increment_failed(n_questions)
            await self.task_repo.update(task)
            yield {
                "type": "progress",
                "completed": task.completed,
                "total": task.total,
                "failed": task.failed,
            }
            return

        questions = result.get("items", result) if isinstance(result, dict) else result
        if not isinstance(questions, list):
            logger.warning("Phase 1 返回格式异常，跳过批次")
            task.increment_failed(n_questions)
            await self.task_repo.update(task)
            yield {
                "type": "progress",
                "completed": task.completed,
                "total": task.total,
                "failed": task.failed,
            }
            return

        batch_chunk_ids = [c.id for c in batch]
        for idx, q in enumerate(questions):
            if q.get("answerable", True) and not q.get("ground_truth_chunks"):
                q["ground_truth_chunks"] = batch_chunk_ids
            yield {
                "type": "question_generated",
                "index": idx,
                "query": q.get("query", ""),
                "type": q.get("type", "factual"),
                "difficulty": q.get("difficulty", "medium"),
            }

        for q in questions:
            async for event in self._process_single_question(
                task, project_id, q, batch, config
            ):
                yield event

            if self.cancel_flag.is_set():
                return
            await self.pause_event.wait()

    async def _process_single_question(
        self,
        task: GenerationTask,
        project_id: str,
        question: dict,
        chunks: list[Chunk],
        config: GenerateConfig,
    ) -> AsyncGenerator[dict, None]:
        """处理单个问题：Phase 2 生成答案 + 入库"""
        query = question.get("query", "").strip()
        answerable = question.get("answerable", True)
        gt_chunks = question.get("ground_truth_chunks", [])
        q_type = question.get("type", "factual")
        difficulty = question.get("difficulty", "medium")

        if not query:
            task.increment_failed()
            await self.task_repo.update(task)
            yield {
                "type": "result",
                "query": "",
                "status": "failed",
                "error": "query 为空",
            }
            yield {
                "type": "progress",
                "completed": task.completed,
                "total": task.total,
                "failed": task.failed,
            }
            return

        reference_answer = ""
        supporting_quotes: list[str] = []
        quality_score = 0.0

        if answerable and gt_chunks:
            yield {"type": "phase_start", "phase": "answer_gen", "query": query}

            chunks_text = self._load_chunks_text(chunks, gt_chunks)
            prompt = answer_generation_prompt(
                chunks_text=chunks_text,
                query=query,
            )

            raw = ""
            try:
                async for token in self.llm.astream(prompt):
                    yield {"type": "llm_token", "content": token}
                    raw += token
                yield {"type": "llm_done", "raw_length": len(raw)}

                answer_result = LLMPort._parse_json_output(raw)
                reference_answer = answer_result.get("reference_answer", "")
                supporting_quotes = answer_result.get("supporting_quotes", [])
            except ValueError as e:
                logger.warning("Phase 2 失败，query: %s", query[:50])
                self.failed_items.append(
                    FailedItem(
                        question=question,
                        chunks=chunks,
                        project_id=project_id,
                        phase="answer_gen",
                        error=str(e),
                    )
                )
                task.increment_failed()
                await self.task_repo.update(task)
                yield {
                    "type": "result",
                    "query": query,
                    "status": "failed",
                    "error": str(e),
                }
                yield {
                    "type": "progress",
                    "completed": task.completed,
                    "total": task.total,
                    "failed": task.failed,
                }
                return

            quality_score = self._compute_quality_score(reference_answer, gt_chunks)

        # 入库
        metadata = {
            "type": q_type,
            "difficulty": difficulty,
            "answerable": answerable,
            "quality_score": quality_score,
            "supporting_quotes": supporting_quotes,
            "source": "llm_generated",
            "groundedness": "unverified",
        }

        record = GoldenRecord(
            project_id=project_id,
            query=query,
            ground_truth_chunks=gt_chunks,
            reference_answer=reference_answer,
            status=GoldenStatus.PENDING_REVIEW,
            metadata=metadata,
        )
        await self.golden_repo.save(record)

        task.increment_completed()
        await self.task_repo.update(task)

        yield {
            "type": "result",
            "query": query,
            "answer": reference_answer,
            "chunk_ids": gt_chunks,
            "quality_score": quality_score,
            "status": "success",
        }
        yield {
            "type": "progress",
            "completed": task.completed,
            "total": task.total,
            "failed": task.failed,
        }

    async def retry_failed(self) -> AsyncGenerator[dict, None]:
        """重试失败项"""
        if not self.failed_items or not self.task:
            return

        items = self.failed_items.copy()
        self.failed_items.clear()

        for item in items:
            async for event in self._process_single_question(
                self.task,
                item.project_id,
                item.question,
                item.chunks,
                self.task.config or GenerateConfig(),
            ):
                yield event

            if self.cancel_flag.is_set():
                return
            await self.pause_event.wait()

    @staticmethod
    def _load_chunks_text(chunks: list[Chunk], chunk_ids: list[str]) -> str:
        """加载指定 chunk 的文本内容"""
        chunk_map = {c.id: c.content for c in chunks}
        texts = []
        for cid in chunk_ids:
            text = chunk_map.get(cid, "")
            if text:
                texts.append(f"[{cid}]\n{text}")
        return "\n\n".join(texts)

    @staticmethod
    def _compute_quality_score(reference_answer: str, gt_chunks: list[str]) -> float:
        """基于多维度计算单条记录质量分（0-1）"""
        score = 1.0
        ans_len = len(reference_answer)
        if ans_len < 20 or ans_len > 300:
            score -= 0.2
        if len(gt_chunks) > 3:
            score -= 0.1
        return round(max(score, 0.0), 2)
