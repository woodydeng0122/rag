from rag.adapters.api.schemas.project import ProjectResponse
from rag.application.results.project_result import ProjectResult


class ProjectPresenter:
    """项目领域实体 → API 响应转换"""

    @staticmethod
    def to_response(result: ProjectResult) -> ProjectResponse:
        p = result.project
        return ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            embed_model_id=p.embed_model_id,
            embed_model_name=result.embed_model_name,
            embed_dimension=p.embed_dimension,
            created_at=p.created_at.isoformat() if p.created_at else "",
            updated_at=p.updated_at.isoformat() if p.updated_at else "",
        )
