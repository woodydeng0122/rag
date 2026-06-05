from rag.domain.entities.embed_model import EmbedModel
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.domain.ports.model_scanner import ModelScannerPort
from rag.domain.ports.project_repository import ProjectRepositoryPort


class EmbedModelUseCase:
    """嵌入模型 CRUD 用例 — 含名称唯一校验、本地模型自动检测、删除前项目引用检查"""

    def __init__(
        self,
        embed_model_repo: EmbedModelRepositoryPort,
        project_repo: ProjectRepositoryPort,
        model_scanner: ModelScannerPort,
    ):
        self._repo = embed_model_repo
        self._project_repo = project_repo
        self._scanner = model_scanner

    async def list(self) -> list[EmbedModel]:
        return await self._repo.get_all()

    async def get(self, model_id: str) -> EmbedModel | None:
        return await self._repo.get_by_id(model_id)

    async def create(self, name: str, dimension: int = 0, description: str = "") -> EmbedModel:
        """创建模型 — 校验名称唯一，尝试从本地 config.json 自动填充维度"""
        existing = await self._repo.get_by_name(name)
        if existing:
            raise ValueError(f"模型名称已存在: {name}")

        # 尝试从本地模型目录读取配置
        config = self._scanner.read_config(name)
        if config:
            dimension = config.get("hidden_size", dimension)
            status = "online"
        else:
            status = "offline" if dimension == 0 else "offline"

        model = EmbedModel(
            name=name,
            dimension=dimension,
            description=description,
            status=status,
        )
        return await self._repo.save(model)

    async def update(self, model_id: str, name: str, dimension: int, description: str = "") -> EmbedModel:
        """更新模型 — 校验存在性和名称唯一"""
        existing = await self._repo.get_by_id(model_id)
        if existing is None:
            raise ValueError(f"模型 {model_id} 不存在")

        same_name = await self._repo.get_by_name(name)
        if same_name and same_name.id != model_id:
            raise ValueError(f"模型名称已存在: {name}")

        existing.name = name
        existing.dimension = dimension
        existing.description = description
        return await self._repo.update(existing)

    async def delete(self, model_id: str) -> bool:
        """删除模型 — 检查是否有项目引用"""
        existing = await self._repo.get_by_id(model_id)
        if existing is None:
            raise ValueError(f"模型 {model_id} 不存在")

        projects = await self._project_repo.list()
        used_by = [p.name for p in projects if p.embed_model_id == model_id]
        if used_by:
            raise ValueError(f"模型正在被项目使用，无法删除: {', '.join(used_by)}")

        return await self._repo.delete(model_id)
