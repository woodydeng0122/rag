from rag.domain.entities.embed_model import EmbedModel, ModelStatus
from rag.domain.value_objects.model_config import ModelConfig
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.domain.ports.model_scanner import ModelScannerPort
from rag.domain.ports.project_repository import ProjectRepositoryPort


class EmbedModelUseCase:
    """嵌入模型 CRUD 用例 — 名称唯一校验、创建流程编排、删除前项目引用检查"""

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

    async def create(self, name: str, dimension: int = 0, description: str = "", config: dict | None = None) -> EmbedModel:
        """创建模型 — 校验名称唯一，尝试从本地 config.json 自动填充维度和状态"""
        existing = await self._repo.get_by_name(name)
        if existing:
            raise ValueError(f"模型名称已存在: {name}")

        # 业务场景：如果未传 config，尝试从本地模型目录读取
        if config is None:
            config = self._scanner.read_config(name)

        model_config = ModelConfig.from_dict(config)

        # 业务场景：有 config → online，无 config → offline；config.hidden_size 可覆盖 dimension
        if config:
            dimension = model_config.hidden_size or dimension
            status = ModelStatus.ONLINE
        else:
            status = ModelStatus.OFFLINE

        model = EmbedModel(
            name=name,
            dimension=dimension,
            description=description,
            status=status,
            config=model_config,
        )

        return await self._repo.save(model)

    async def update(self, model_id: str, name: str, description: str = "") -> EmbedModel:
        """更新模型 — 仅允许修改名称和备注"""
        existing = await self._repo.get_by_id(model_id)
        if existing is None:
            raise ValueError(f"模型 {model_id} 不存在")

        same_name = await self._repo.get_by_name(name)
        if same_name and same_name.id != model_id:
            raise ValueError(f"模型名称已存在: {name}")

        existing.update_profile(name, description)
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
