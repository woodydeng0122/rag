import json
from pathlib import Path

from rag.domain.ports.model_scanner import ModelScannerPort, ScannedModel

# 嵌入模型保存时产生的子目录（如 1_Pooling、2_Dense 等），不应作为独立模型扫描
_EMBED_SUBDIR_PREFIXES = frozenset({"1_Pooling", "2_Dense", "2_Pooling", "3_Dense", "3_Pooling"})


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
            # 跳过嵌入模型的子目录（如 1_Pooling）
            if model_dir.name in _EMBED_SUBDIR_PREFIXES:
                continue

            # 模型名 = 相对于 models/ 的路径，如 BAAI/bge-small-zh-v1.5
            relative = model_dir.relative_to(self._models_dir)
            name = str(relative).replace("\\", "/")

            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            # 通过 config.json 的 architectures 判定模型类型
            model_type = self._detect_model_type(model_dir, config)

            if model_type == "embed":
                dimension = config.get("hidden_size")
                if dimension is None:
                    continue
            else:
                dimension = 0

            results.append(ScannedModel(
                name=name,
                model_type=model_type,
                dimension=dimension,
                path=str(model_dir),
                metadata=config,
            ))

        return results

    @staticmethod
    def _detect_model_type(model_dir: Path, config: dict) -> str:
        """根据目录结构和 config 内容判定模型类型 — reranker vs embed

        判定优先级：
        1. 存在 modules.json（sentence-transformers 嵌入模型标识）→ embed
        2. architectures 包含 SequenceClassification（cross-encoder 标识）→ reranker
        3. 兜底：有 1_Pooling 子目录 → embed，否则 → reranker
        """
        if (model_dir / "modules.json").exists():
            return "embed"

        architectures = config.get("architectures", [])
        if any("SequenceClassification" in str(a) for a in architectures):
            return "reranker"

        # 兜底：嵌入模型有 1_Pooling 子目录，重排模型没有
        return "embed" if (model_dir / "1_Pooling").exists() else "reranker"

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
