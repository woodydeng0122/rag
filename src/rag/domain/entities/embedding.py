from dataclasses import dataclass


@dataclass
class Embedding:
    """向量嵌入实体 — 关联 chunk_id 与向量"""
    chunk_id: str
    vector: list[float]
