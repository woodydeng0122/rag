from abc import ABC, abstractmethod


class FileStoragePort(ABC):
    """文件存储端口 — 文件读写/目录创建的抽象"""

    @abstractmethod
    def mkdir(self, path: str) -> None:
        """创建目录（含父目录）"""
        ...

    @abstractmethod
    def write_bytes(self, path: str, data: bytes) -> None:
        """写入二进制文件"""
        ...

    @abstractmethod
    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """读取文本文件"""
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        """判断文件是否存在"""
        ...
