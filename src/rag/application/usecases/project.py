from rag.application.results.project_result import ProjectResult
from rag.domain.entities.project import Project
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort


class ProjectUseCase:
    """项目 CRUD 用例 — 包含模型校验等业务逻辑"""

    def __init__(
        self,
        project_repo: ProjectRepositoryPort,
        embed_model_repo: EmbedModelRepositoryPort,
    ):
        self._project_repo = project_repo
        self._embed_model_repo = embed_model_repo

    async def create(self, name: str, description: str, embed_model_id: str) -> Project:
        """创建项目 — 校验嵌入模型存在且可用，维度与系统一致"""
        embed_model = await self._embed_model_repo.get_by_id(embed_model_id)
        if embed_model is None:
            raise ValueError("嵌入模型不存在")
        if not embed_model.is_online:
            raise ValueError(f"嵌入模型不可用: {embed_model.name} (status={embed_model.status.value})")

        project = Project(
            name=name,
            description=description,
            embed_model_id=embed_model_id,
            embed_dimension=embed_model.dimension,
        )
        return await self._project_repo.save(project)

    async def get(self, project_id: str) -> Project | None:
        return await self._project_repo.get_by_id(project_id)

    async def list(self) -> list[Project]:
        return await self._project_repo.list()

    async def update(self, project_id: str, name: str, description: str) -> Project:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise ValueError(f"项目 {project_id} 不存在")
        project.update_profile(name, description)
        return await self._project_repo.update(project)

    async def delete(self, project_id: str) -> bool:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise ValueError(f"项目 {project_id} 不存在")
        return await self._project_repo.delete(project_id)

    # ── 带 embed_model_name 的查询 ──────────────────────────

    async def get_with_model_name(self, project_id: str) -> ProjectResult | None:
        """查询项目并附带嵌入模型名称"""
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            return None
        return await self._to_result(project)

    async def list_with_model_name(self) -> list[ProjectResult]:
        """列出所有项目并附带嵌入模型名称"""
        projects = await self._project_repo.list()
        return [await self._to_result(p) for p in projects]

    async def _to_result(self, project: Project) -> ProjectResult:
        embed_model_name = ""
        if project.embed_model_id:
            embed_model = await self._embed_model_repo.get_by_id(project.embed_model_id)
            if embed_model:
                embed_model_name = embed_model.name
        return ProjectResult(project=project, embed_model_name=embed_model_name)
