import hashlib
import io
import zipfile
from pathlib import Path
from uuid import uuid4

from rag.domain.entities.document import Document
from rag.domain.ports.document_repository import DocumentRepositoryPort
from rag.domain.ports.file_storage import FileStoragePort


ALLOWED_EXTENSIONS = {".md", ".txt", ".pdf"}
ALLOWED_ARCHIVE_EXTENSIONS = {".zip"}


class UploadUseCase:
    """上传用例 — 接收文件/zip，存储到 docs/{upload_id}/，创建 document 记录"""

    def __init__(
        self,
        document_repo: DocumentRepositoryPort,
        file_storage: FileStoragePort,
    ):
        self._document_repo = document_repo
        self._file_storage = file_storage

    async def execute(
        self,
        project_id: str,
        filename: str,
        file_content: bytes,
        splitter_strategy: str = "section_heading",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        splitter_min_chars: int = 200,
        splitter_max_chars: int = 2000,
    ) -> list[Document]:
        upload_id = str(uuid4())
        docs_dir = f"docs/{upload_id}"
        self._file_storage.mkdir(docs_dir)

        # 判断是否为允许的压缩包
        ext = Path(filename).suffix.lower()
        if ext in ALLOWED_ARCHIVE_EXTENSIONS:
            return await self._handle_zip(
                file_content, docs_dir, upload_id, project_id,
                splitter_strategy, chunk_size, chunk_overlap,
                splitter_min_chars, splitter_max_chars,
            )
        else:
            # 单文件
            if ext not in ALLOWED_EXTENSIONS:
                allowed = ALLOWED_EXTENSIONS | ALLOWED_ARCHIVE_EXTENSIONS
                raise ValueError(f"不支持的文件类型: {ext}，仅支持 {allowed}")

            file_path = f"{docs_dir}/{filename}"
            self._file_storage.write_bytes(file_path, file_content)
            checksum = hashlib.sha256(file_content).hexdigest()

            doc = Document(
                project_id=project_id,
                filename=filename,
                file_path=file_path,
                file_size=len(file_content),
                file_type=ext.lstrip("."),
                checksum=checksum,
                status="uploaded",
                splitter_strategy=splitter_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                splitter_min_chars=splitter_min_chars,
                splitter_max_chars=splitter_max_chars,
            )
            saved = await self._document_repo.save(doc)
            return [saved]

    async def _handle_zip(
        self,
        file_content: bytes,
        docs_dir: str,
        upload_id: str,
        project_id: str,
        splitter_strategy: str,
        chunk_size: int,
        chunk_overlap: int,
        splitter_min_chars: int,
        splitter_max_chars: int,
    ) -> list[Document]:
        """解压 zip 并为每个支持的文件创建 document 记录"""
        zip_buffer = io.BytesIO(file_content)
        documents = []

        with zipfile.ZipFile(zip_buffer, "r") as zf:
            for entry in zf.namelist():
                # 跳过目录和隐藏文件
                if entry.endswith("/") or Path(entry).name.startswith("."):
                    continue

                ext = Path(entry).suffix.lower()
                if ext not in ALLOWED_EXTENSIONS:
                    continue

                # 保持目录结构解压
                entry_content = zf.read(entry)
                target_path = f"{docs_dir}/{entry}"
                parent_dir = str(Path(target_path).parent)
                self._file_storage.mkdir(parent_dir)
                self._file_storage.write_bytes(target_path, entry_content)

                checksum = hashlib.sha256(entry_content).hexdigest()

                doc = Document(
                    project_id=project_id,
                    filename=Path(entry).name,
                    file_path=target_path,
                    file_size=len(entry_content),
                    file_type=ext.lstrip("."),
                    checksum=checksum,
                    status="uploaded",
                    splitter_strategy=splitter_strategy,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    splitter_min_chars=splitter_min_chars,
                    splitter_max_chars=splitter_max_chars,
                )
                saved = await self._document_repo.save(doc)
                documents.append(saved)

        return documents
