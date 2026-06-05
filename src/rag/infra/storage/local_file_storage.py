from pathlib import Path

from rag.domain.ports.file_storage import FileStoragePort


class LocalFileStorage(FileStoragePort):
    """本地文件系统实现"""

    def mkdir(self, path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    def write_bytes(self, path: str, data: bytes) -> None:
        Path(path).write_bytes(data)
