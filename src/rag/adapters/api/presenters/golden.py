from rag.adapters.api.schemas.golden import (
    GoldenResponse,
    GoldenStatusEnum,
)
from rag.domain.entities.golden_record import GoldenRecord, GoldenStatus as DomainGoldenStatus

# 领域枚举 → API 枚举映射
_DOMAIN_TO_API_GOLDEN_STATUS = {
    DomainGoldenStatus.PENDING_REVIEW: GoldenStatusEnum.PENDING_REVIEW,
    DomainGoldenStatus.APPROVED: GoldenStatusEnum.APPROVED,
    DomainGoldenStatus.REJECTED: GoldenStatusEnum.REJECTED,
}


class GoldenPresenter:
    """黄金记录领域实体 → API 响应转换"""

    @staticmethod
    def to_response(r: GoldenRecord) -> GoldenResponse:
        return GoldenResponse(
            id=r.id,
            project_id=r.project_id,
            query=r.query,
            ground_truth_chunks=r.ground_truth_chunks,
            reference_answer=r.reference_answer or "",
            status=_DOMAIN_TO_API_GOLDEN_STATUS[r.status],
            created_at=r.created_at.isoformat() if r.created_at else "",
            metadata=r.metadata if r.metadata else {},
        )
