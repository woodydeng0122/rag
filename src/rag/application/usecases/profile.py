from rag.domain.entities.profile import Profile
from rag.domain.ports.profile_repository import ProfileRepositoryPort
from rag.domain.ports.project_repository import ProjectRepositoryPort


class ProfileUseCase:
    """用户配置用例 — 获取/更新激活项目"""

    def __init__(
        self,
        profile_repo: ProfileRepositoryPort,
        project_repo: ProjectRepositoryPort,
    ):
        self._profile_repo = profile_repo
        self._project_repo = project_repo

    async def get(self) -> Profile:
        return await self._profile_repo.get()

    async def update(self, active_project_id: str | None) -> Profile:
        if active_project_id is not None:
            project = await self._project_repo.get_by_id(active_project_id)
            if project is None:
                raise ValueError("项目不存在")
        return await self._profile_repo.upsert(active_project_id)
