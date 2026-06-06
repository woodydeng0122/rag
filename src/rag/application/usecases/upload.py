import hashlib
import io
import zipfile
from pathlib import Path
from uuid import uuid4

from rag.domain.entities.document import Document, DocumentStatus
from rag.domain.value_objects.splitter_config import SplitterConfig
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
        splitter_config: SplitterConfig | None = None,
    ) -> list[Document]:
        config = splitter_config or SplitterConfig()
        upload_id = str(uuid4())
        docs_dir = f"docs/{upload_id}"
        self._file_storage.mkdir(docs_dir)

        # 判断是否为允许的压缩包
        ext = Path(filename).suffix.lower()
        if ext in ALLOWED_ARCHIVE_EXTENSIONS:
            return await self._handle_zip(
                file_content, docs_dir, upload_id, project_id, config,
            )
        else:
            # 单文件
            if ext not in ALLOWED_EXTENSIONS:
                allowed = ALLOWED_EXTENSIONS | ALLOWED_ARCHIVE_EXTENSIONS
                raise ValueError(f"不支持的文件类型: {ext}，仅支持 {allowed}")

            storage_key = f"{docs_dir}/{filename}"
            self._file_storage.write_bytes(storage_key, file_content)
            checksum = hashlib.sha256(file_content).hexdigest()

            doc = Document(
                project_id=project_id,
                filename=filename,
                storage_key=storage_key,
                file_size=len(file_content),
                file_type=ext.lstrip("."),
                checksum=checksum,
                status=DocumentStatus.UPLOADED,
                splitter_config=config,
            )
            saved = await self._document_repo.save(doc)
            return [saved]

    async def _handle_zip(
        self,
        file_content: bytes,
        docs_dir: str,
        upload_id: str,
        project_id: str,
        splitter_config: SplitterConfig,
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
                target_key = f"{docs_dir}/{entry}"
                parent_dir = str(Path(target_key).parent)
                self._file_storage.mkdir(parent_dir)
                self._file_storage.write_bytes(target_key, entry_content)

                checksum = hashlib.sha256(entry_content).hexdigest()

                doc = Document(
                    project_id=project_id,
                    filename=Path(entry).name,
                    storage_key=target_key,
                    file_size=len(entry_content),
                    file_type=ext.lstrip("."),
                    checksum=checksum,
                    status=DocumentStatus.UPLOADED,
                    splitter_config=splitter_config,
                )
                saved = await self._document_repo.save(doc)
                documents.append(saved)

        return documents
