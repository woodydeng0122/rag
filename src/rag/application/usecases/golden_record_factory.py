from rag.domain.entities.golden_record import GoldenRecord, GoldenStatus
from rag.domain.value_objects.quality_scorer import QualityScorer


class GoldenRecordFactory:
    """从 LLM 生成结果构建 GoldenRecord 实体"""

    def __init__(self, quality_scorer: QualityScorer | None = None):
        self._scorer = quality_scorer or QualityScorer()

    def create(
        self,
        project_id: str,
        query: str,
        answerable: bool,
        gt_chunks: list[str],
        reference_answer: str,
        supporting_quotes: list[str],
        q_type: str,
        difficulty: str,
    ) -> GoldenRecord:
        """从单条 LLM 生成结果构建 GoldenRecord"""
        quality_score = 0.0
        if answerable and gt_chunks:
            quality_score = self._scorer.score(reference_answer, gt_chunks)

        metadata = {
            "type": q_type,
            "difficulty": difficulty,
            "answerable": answerable,
            "quality_score": quality_score,
            "supporting_quotes": supporting_quotes,
            "source": "llm_generated",
            "groundedness": "unverified",
        }

        return GoldenRecord(
            project_id=project_id,
            query=query,
            ground_truth_chunks=gt_chunks,
            reference_answer=reference_answer,
            status=GoldenStatus.PENDING_REVIEW,
            metadata=metadata,
        )
