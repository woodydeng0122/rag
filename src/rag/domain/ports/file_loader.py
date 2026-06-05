from abc import ABC, abstractmethod


class FileLoaderPort(ABC):
    """单文件加载端口 — 加载单个文件的抽象"""

    @abstractmethod
    def load_file_txt(self, path: str) -> str: ...

    @abstractmethod
    def load_file_pdf(self, path: str) -> str: ...
