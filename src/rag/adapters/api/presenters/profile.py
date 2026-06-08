from rag.adapters.api.schemas.profile import ProfileResponse
from rag.domain.entities.profile import Profile


class ProfilePresenter:
    """用户配置领域实体 → API 响应转换"""

    @staticmethod
    def to_response(p: Profile) -> ProfileResponse:
        return ProfileResponse(
            id=p.id,
            active_project_id=p.active_project_id,
        )
