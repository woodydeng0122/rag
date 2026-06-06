from dataclasses import dataclass


@dataclass
class Embedding:
    """向量嵌入实体 — 关联 chunk_id 与向量"""

    chunk_id: str
    vector: list[float]
    embedder_model: str = ""

    @property
    def dimension(self) -> int:
        """向量维度 — 由 vector 派生，不单独存储"""
        return len(self.vector)

    def __post_init__(self):
        if not self.chunk_id:
            raise ValueError("chunk_id 不能为空")
        if not self.vector:
            raise ValueError("vector 不能为空")
