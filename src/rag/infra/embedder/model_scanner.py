import json
from pathlib import Path

from rag.domain.ports.model_scanner import ModelScannerPort, ScannedModel


class ModelScanner(ModelScannerPort):
    """扫描本地 models/ 目录，发现可用的 SentenceTransformer 模型"""

    def __init__(self, models_dir: str = "models"):
        self._models_dir = Path(models_dir)

    def scan(self) -> list[ScannedModel]:
        """递归扫描 models/ 目录，查找包含 config.json 的子目录"""
        results: list[ScannedModel] = []
        if not self._models_dir.exists():
            return results

        for config_path in sorted(self._models_dir.rglob("config.json")):
            model_dir = config_path.parent
            # 模型名 = 相对于 models/ 的路径，如 BAAI/bge-small-zh-v1.5
            relative = model_dir.relative_to(self._models_dir)
            name = str(relative).replace("\\", "/")

            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                dimension = config.get("hidden_size")
                if dimension is None:
                    continue
            except (json.JSONDecodeError, OSError):
                continue

            results.append(ScannedModel(
                name=name,
                dimension=dimension,
                path=str(model_dir),
                metadata=config,
            ))

        return results

    def read_config(self, model_name: str) -> dict | None:
        """读取指定模型的 config.json，返回完整内容或 None"""
        config_path = self._models_dir / model_name / "config.json"
        if not config_path.exists():
            return None
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def existing_model_names(self) -> set[str]:
        """返回 models/ 目录下已存在的模型名称集合"""
        return {m.name for m in self.scan()}
