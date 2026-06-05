from pathlib import Path
from rag.domain.ports.dir_loader import DirLoaderPort
from rag.domain.ports.file_loader import FileLoaderPort


class FileDocumentLoader(DirLoaderPort, FileLoaderPort):
    """基于文件系统的文档加载器实现 — 同时满足目录加载和文件加载两个端口"""

    def load_file_txt(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def load_file_pdf(self, path: str) -> str:
        from pypdf import PdfReader
        reader = PdfReader(path)
        doc = "\n\n".join(page.extract_text() for page in reader.pages)
        print(f"文档字数: {len(doc) / 10000:.1f} 万字")
        return doc

    def load_dir_md(self, dir: str) -> list[dict]:
        root = Path(dir)
        result = []
        for p in sorted(root.rglob("*.md")):
            if not p.is_file():
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            if not text.strip():
                continue
            rel = str(p.relative_to(root))
            subdir = str(p.parent.relative_to(root)) if str(p.parent) != str(root) else ""
            result.append({"path": rel, "subdir": subdir, "text": text})
        return result
