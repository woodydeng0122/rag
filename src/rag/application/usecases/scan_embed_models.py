from rag.domain.entities.embed_model import EmbedModel, ModelStatus
from rag.domain.value_objects.model_config import ModelConfig
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.domain.ports.model_scanner import ModelScannerPort


class ScanEmbedModelsUseCase:
    """扫描本地 models/ 目录，upsert embed_model 表，更新 status"""

    def __init__(
        self,
        embed_model_repo: EmbedModelRepositoryPort,
        model_scanner: ModelScannerPort,
    ):
        self._repo = embed_model_repo
        self._scanner = model_scanner

    async def execute(self) -> list[EmbedModel]:
        # 1. 扫描本地目录
        scanned = self._scanner.scan()
        scanned_names = {s.name for s in scanned}

        # 2. Upsert 扫描到的模型 — 业务场景：本地存在 → online
        for s in scanned:
            model_config = ModelConfig.from_dict(s.metadata)
            dimension = model_config.hidden_size or s.dimension
            model = EmbedModel(
                name=s.name,
                dimension=dimension,
                status=ModelStatus.ONLINE,
                config=model_config,
            )
            await self._repo.save(model)

        # 3. 将不在本地的模型标记为 offline — 业务场景：本地不存在 → offline
        all_models = await self._repo.get_all()
        for m in all_models:
            if m.name not in scanned_names and m.is_online:
                m.go_offline()
                await self._repo.update(m)

        # 4. 返回更新后的完整列表
        return await self._repo.get_all()
