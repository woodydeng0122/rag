from rag.adapters.api.schemas.golden_dataset import (
    EvaluationMetricsResponse,
    GenerationTaskResponse,
    GoldenDatasetResponse,
    GoldenStatusEnum,
    TaskStatusEnum,
)
from rag.domain.entities.generation_task import GenerationTask, TaskStatus as DomainTaskStatus
from rag.domain.entities.golden_record import GoldenRecord, GoldenStatus as DomainGoldenStatus

# 领域枚举 → API 枚举映射
_DOMAIN_TO_API_GOLDEN_STATUS = {
    DomainGoldenStatus.PENDING_REVIEW: GoldenStatusEnum.PENDING_REVIEW,
    DomainGoldenStatus.APPROVED: GoldenStatusEnum.APPROVED,
    DomainGoldenStatus.REJECTED: GoldenStatusEnum.REJECTED,
}

_DOMAIN_TO_API_TASK_STATUS = {
    DomainTaskStatus.RUNNING: TaskStatusEnum.RUNNING,
    DomainTaskStatus.PAUSED: TaskStatusEnum.PAUSED,
    DomainTaskStatus.CANCELLED: TaskStatusEnum.CANCELLED,
    DomainTaskStatus.COMPLETED: TaskStatusEnum.COMPLETED,
    DomainTaskStatus.FAILED: TaskStatusEnum.FAILED,
}


class GoldenDatasetPresenter:
    """黄金记录领域实体 → API 响应转换"""

    @staticmethod
    def to_response(r: GoldenRecord) -> GoldenDatasetResponse:
        evaluation = None
        if r.evaluation:
            evaluation = EvaluationMetricsResponse(
                retrieved_chunk_ids=r.evaluation.retrieved_chunk_ids or [],
                is_hit=r.evaluation.is_hit,
                hit_rank=r.evaluation.hit_rank,
                evaluated_at=(
                    r.evaluation.evaluated_at.isoformat()
                    if r.evaluation.evaluated_at
                    else None
                ),
            )
        return GoldenDatasetResponse(
            id=r.id,
            project_id=r.project_id,
            query=r.query,
            ground_truth_chunks=r.ground_truth_chunks,
            reference_answer=r.reference_answer or "",
            status=_DOMAIN_TO_API_GOLDEN_STATUS[r.status],
            evaluation=evaluation,
            created_at=r.created_at.isoformat() if r.created_at else "",
            metadata=r.metadata if r.metadata else {},
        )

    @staticmethod
    def to_task_response(t: GenerationTask) -> GenerationTaskResponse:
        return GenerationTaskResponse(
            id=t.id,
            project_id=t.project_id,
            status=_DOMAIN_TO_API_TASK_STATUS[t.status],
            total=t.total,
            completed=t.completed,
            failed=t.failed,
            document_ids=t.document_ids or [],
            chunk_ids=t.chunk_ids or [],
            config=t.config.to_dict() if t.config else {},
            error_message=t.error_message or "",
            created_at=t.created_at.isoformat() if t.created_at else "",
            updated_at=t.updated_at.isoformat() if t.updated_at else None,
            finished_at=t.finished_at.isoformat() if t.finished_at else None,
        )
