from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ScannedModel:
    """扫描发现的模型信息"""
    name: str
    dimension: int
    path: str
    metadata: dict  # config.json 完整内容


class ModelScannerPort(ABC):
    """模型扫描器端口 — 扫描本地模型目录的抽象"""

    @abstractmethod
    def scan(self) -> list[ScannedModel]: ...

    @abstractmethod
    def existing_model_names(self) -> set[str]: ...

    @abstractmethod
    def read_config(self, model_name: str) -> dict | None: ...
