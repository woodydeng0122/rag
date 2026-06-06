import asyncio
import json
import logging

from rag.domain.entities.chunk import Chunk
from rag.domain.entities.generate_config import GenerateConfig
from rag.domain.entities.generation_task import GenerationTask, TaskStatus
from rag.domain.entities.golden_record import GoldenRecord, GoldenStatus
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.domain.ports.generation_task_repository import GenerationTaskRepositoryPort
from rag.domain.ports.golden_dataset_repository import GoldenDatasetRepositoryPort
from rag.domain.ports.llm import LLMPort

logger = logging.getLogger(__name__)


class GenerateGoldenUseCase:
    """LLM 驱动的黄金数据集两阶段生成用例"""

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

    async def execute(
        self,
        project_id: str,
        document_ids: list[str] | None = None,
        chunk_ids: list[str] | None = None,
        config: GenerateConfig | None = None,
    ) -> GenerationTask:
        """创建生成任务并启动后台协程"""
        if config is None:
            config = GenerateConfig()

        # 加载目标 chunks
        chunks_by_doc: dict[str, list[Chunk]] = {}
        if chunk_ids:
            all_chunks = await self.chunk_repo.list_by_project(project_id, limit=10000, offset=0)
            selected = {c for c in all_chunks if c.id in set(chunk_ids)}
            for c in selected:
                doc_id = c.source_file
                chunks_by_doc.setdefault(doc_id, []).append(c)
        elif document_ids:
            for doc_id in document_ids:
                doc_chunks = await self.chunk_repo.list_by_document(doc_id)
                chunks_by_doc[doc_id] = doc_chunks
        else:
            raise ValueError("必须提供 document_ids 或 chunk_ids")

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

        # 启动后台协程
        asyncio.create_task(
            self._run_generation(task, project_id, chunks_by_doc, config)
        )

        return task

    async def _run_generation(
        self,
        task: GenerationTask,
        project_id: str,
        chunks_by_doc: dict[str, list[Chunk]],
        config: GenerateConfig,
    ) -> None:
        """后台协程：串行执行两阶段生成"""
        try:
            for doc_id, chunks in chunks_by_doc.items():
                chunks.sort(key=lambda c: c.index)
                total_chars = sum(len(c.content) for c in chunks)

                if total_chars <= config.file_char_threshold:
                    await self._process_whole_doc(task, project_id, chunks, config)
                else:
                    await self._process_chunk_batches(task, project_id, chunks, config)

            task.complete()
            await self.task_repo.update(task)

        except Exception as e:
            logger.exception("生成任务 %s 异常", task.id)
            task.fail(str(e))
            await self.task_repo.update(task)

    async def _process_whole_doc(
        self,
        task: GenerationTask,
        project_id: str,
        chunks: list[Chunk],
        config: GenerateConfig,
    ) -> None:
        """整篇文档模式：一次 LLM 调用生成所有问题"""
        full_doc = "\n\n".join(c.content for c in chunks)
        chunks_info = json.dumps(
            [{"id": c.id, "heading": c.heading, "index": c.index} for c in chunks],
            ensure_ascii=False,
        )
        type_dist = self._format_type_distribution(config.question_types)
        n_questions = len(chunks) * config.per_chunk

        prompt = (
            "你是 RAG 评测数据生成专家。仔细阅读以下完整文档，\n"
            f"生成 {n_questions} 个真实用户可能提出的问题。\n\n"
            "规则：\n"
            "- 不要考虑文档如何被切分，只关注文档传达的知识点\n"
            f"- 风格贴近真实用户提问（{config.user_persona}）\n"
            f"- 覆盖不同类型：{type_dist}\n"
            "- 不要直接复制原文句子作为问题\n"
            "- difficulty 按\u201c检索难度\u201d标注：\n"
            "  - easy：query 关键词与原文高度重叠\n"
            "  - medium：query 用词与原文有差异\n"
            "  - hard：query 需要推理/跨段综合\n"
            "- 对于 comparison 类型，问题需要对比文档中不同部分的内容\n"
            "- 对于 unanswerable 类型，生成看起来相关但文档无法回答的问题\n\n"
            f"文档：\n{full_doc}\n\n"
            f"文档分块信息（用于映射）：\n{chunks_info}\n\n"
            "输出格式（JSON 数组）：\n"
            '[{"query": "...", "type": "factual|procedural|reasoning|comparison|unanswerable", '
            '"difficulty": "easy|medium|hard", "answerable": true|false, '
            '"ground_truth_chunks": ["chunk_id_1"]}]'
        )

        try:
            result = self.llm.generate_json(prompt)
        except ValueError:
            logger.warning("整篇文档 Phase 1 失败，跳过文档")
            task.record_failure(n_questions)
            await self.task_repo.update(task)
            return

        questions = result.get("items", result) if isinstance(result, dict) else result
        if not isinstance(questions, list):
            logger.warning("Phase 1 返回格式异常，跳过文档")
            task.record_failure(n_questions)
            await self.task_repo.update(task)
            return

        for q in questions:
            await self._process_single_question(task, project_id, q, chunks, config)

    async def _process_chunk_batches(
        self,
        task: GenerationTask,
        project_id: str,
        chunks: list[Chunk],
        config: GenerateConfig,
    ) -> None:
        """分批 chunk 模式：3 chunk 为一轮"""
        batch_size = config.chunk_batch_size
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            await self._process_single_batch(task, project_id, batch, config)

    async def _process_single_batch(
        self,
        task: GenerationTask,
        project_id: str,
        batch: list[Chunk],
        config: GenerateConfig,
    ) -> None:
        """处理单个 chunk 批次"""
        chunks_text = json.dumps(
            [{"id": c.id, "content": c.content[:800]} for c in batch],
            ensure_ascii=False,
        )
        type_dist = self._format_type_distribution(config.question_types)
        n_questions = len(batch) * config.per_chunk

        prompt = (
            "你是 RAG 评测数据生成专家。阅读以下文本片段，\n"
            f"生成 {n_questions} 个真实用户可能提出的问题。\n\n"
            "规则：\n"
            f"- 风格贴近真实用户提问（{config.user_persona}）\n"
            f"- 覆盖不同类型：{type_dist}\n"
            "- 不要直接复制原文句子作为问题\n"
            "- difficulty 按\u201c检索难度\u201d标注\n"
            "- 对于 unanswerable 类型，生成与片段主题相关但片段无法回答的问题\n\n"
            f"文本片段：\n{chunks_text}\n\n"
            "输出格式（JSON 数组）：\n"
            '[{"query": "...", "type": "factual|procedural|reasoning|comparison|unanswerable", '
            '"difficulty": "easy|medium|hard", "answerable": true|false}]'
        )

        try:
            result = self.llm.generate_json(prompt)
        except ValueError:
            logger.warning("批次 Phase 1 失败，跳过")
            task.record_failure(n_questions)
            await self.task_repo.update(task)
            return

        questions = result.get("items", result) if isinstance(result, dict) else result
        if not isinstance(questions, list):
            logger.warning("Phase 1 返回格式异常，跳过批次")
            task.record_failure(n_questions)
            await self.task_repo.update(task)
            return

        batch_chunk_ids = [c.id for c in batch]
        for q in questions:
            # 分批模式下 ground_truth 直接为当前 batch 的 chunk_ids
            if q.get("answerable", True) and not q.get("ground_truth_chunks"):
                q["ground_truth_chunks"] = batch_chunk_ids
            await self._process_single_question(task, project_id, q, batch, config)

    async def _process_single_question(
        self,
        task: GenerationTask,
        project_id: str,
        question: dict,
        chunks: list[Chunk],
        config: GenerateConfig,
    ) -> None:
        """处理单个问题：Phase 2 生成答案 + 入库"""
        query = question.get("query", "").strip()
        answerable = question.get("answerable", True)
        gt_chunks = question.get("ground_truth_chunks", [])
        q_type = question.get("type", "factual")
        difficulty = question.get("difficulty", "medium")

        if not query:
            task.record_failure()
            await self.task_repo.update(task)
            return

        reference_answer = ""
        supporting_quotes: list[str] = []
        quality_score = 0.0

        if answerable and gt_chunks:
            # Phase 2: 生成参考答案
            chunks_text = self._load_chunks_text(chunks, gt_chunks)
            prompt = (
                "根据以下文本片段，回答问题。\n\n"
                "规则：\n"
                "- 答案完全基于给定文本，不引入外部知识\n"
                "- 简洁准确，20-300 字\n"
                "- 如果文本中没有答案，回答\u201c该问题在文档中无对应信息\u201d\n\n"
                f"文本片段：\n{chunks_text}\n\n"
                f"问题：{query}\n\n"
                '输出格式（JSON）：\n{"reference_answer": "...", "supporting_quotes": ["原文片段1"]}'
            )

            try:
                answer_result = self.llm.generate_json(prompt)
                reference_answer = answer_result.get("reference_answer", "")
                supporting_quotes = answer_result.get("supporting_quotes", [])
            except ValueError:
                logger.warning("Phase 2 失败，query: %s", query[:50])
                task.record_failure()
                await self.task_repo.update(task)
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

        task.record_success()
        await self.task_repo.update(task)

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

    @staticmethod
    def _format_type_distribution(question_types: dict[str, float]) -> str:
        """格式化问题类型分布描述"""
        parts = [f"{k} {int(v * 100)}%" for k, v in question_types.items()]
        return "、".join(parts)
