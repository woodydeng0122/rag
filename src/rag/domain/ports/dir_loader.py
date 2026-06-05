from abc import ABC, abstractmethod


class DirLoaderPort(ABC):
    """目录加载端口 — 从目录批量加载文档的抽象"""

    @abstractmethod
    def load_dir_md(self, dir: str) -> list[dict]: ...
