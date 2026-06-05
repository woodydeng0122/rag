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
        if embed_model.status != "online":
            raise ValueError(f"嵌入模型不可用: {embed_model.name} (status={embed_model.status})")

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
        project.name = name
        project.description = description
        return await self._project_repo.update(project)

    async def delete(self, project_id: str) -> bool:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise ValueError(f"项目 {project_id} 不存在")
        return await self._project_repo.delete(project_id)
