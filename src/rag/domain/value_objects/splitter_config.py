from dataclasses import dataclass


@dataclass
class SplitterConfig:
    """分块配置值对象"""

    strategy: str = "section_heading"
    chunk_size: int = 500
    chunk_overlap: int = 50
    min_chars: int = 200
    max_chars: int = 2000

    def to_splitter_kwargs(self) -> dict:
        """根据策略构建分块器参数 — 纯函数，SplitterConfig 自己的事"""
        if self.strategy == "fixed":
            return {"chunk_size": self.chunk_size, "overlap": self.chunk_overlap}
        if self.strategy == "section_heading":
            return {"min_chars": self.min_chars, "max_chars": self.max_chars}
        return {}
