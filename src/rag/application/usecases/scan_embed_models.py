from rag.domain.entities.embed_model import EmbedModel
from rag.domain.ports.embed_model_repository import EmbedModelRepositoryPort
from rag.infra.embedder.model_scanner import ModelScanner


class ScanEmbedModelsUseCase:
    """扫描本地 models/ 目录，upsert embed_model 表，更新 status"""

    def __init__(
        self,
        embed_model_repo: EmbedModelRepositoryPort,
        model_scanner: ModelScanner,
    ):
        self._repo = embed_model_repo
        self._scanner = model_scanner

    async def execute(self) -> list[EmbedModel]:
        # 1. 扫描本地目录
        scanned = self._scanner.scan()
        scanned_names = {s.name for s in scanned}

        # 2. Upsert 扫描到的模型（status=online）
        for s in scanned:
            model = EmbedModel(
                name=s.name,
                dimension=s.dimension,
                status="online",
            )
            await self._repo.save(model)

        # 3. 将不在本地的模型标记为 offline
        all_models = await self._repo.get_all()
        for m in all_models:
            if m.name not in scanned_names and m.status != "offline":
                await self._repo.update_status(m.id, "offline")

        # 4. 返回更新后的完整列表
        return await self._repo.get_all()
