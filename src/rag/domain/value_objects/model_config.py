from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelConfig:
    """模型配置值对象 — 封装 config.json 的结构化访问

    已知字段提取为类型属性，原始数据保留用于持久化往返。
    """

    hidden_size: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ModelConfig":
        if not data:
            return cls()
        return cls(hidden_size=data.get("hidden_size"), raw=data)

    def to_dict(self) -> dict[str, Any]:
        result = dict(self.raw)
        if self.hidden_size is not None:
            result["hidden_size"] = self.hidden_size
        return result
