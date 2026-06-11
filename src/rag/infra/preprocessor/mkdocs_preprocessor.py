import re
from pathlib import Path

from rag.domain.ports.markdown_preprocessor import MarkdownPreprocessorPort


class MkDocsPreprocessor(MarkdownPreprocessorPort):
    """MkDocs/Material 主题 Markdown 预处理 — 解析文件包含、剥离锚点标记"""

    def __init__(self, base_dir: str = ""):
        self._base_dir = Path(base_dir) if base_dir else Path.cwd()

    def preprocess(self, text: str, source_path: str = "") -> str:
        text = self._resolve_includes(text, source_path)
        text = self._strip_heading_anchors(text)
        return text

    # -- 文件包含 {* .../.../file.py hl[1] *} --

    _INCLUDE_RE = re.compile(r"\{\*\s*(.+?)\s*\*\}")

    def _resolve_includes(self, text: str, source_path: str) -> str:
        source_dir = self._base_dir
        if source_path:
            candidate = self._base_dir / source_path
            if candidate.is_file():
                source_dir = candidate.parent

        def _replace(match: re.Match) -> str:
            raw = match.group(1).strip()
            # 去掉尾部参数如 hl[1], linenums="1"
            path_part = re.split(r"\s+", raw, maxsplit=1)[0]
            full_path = source_dir / path_part
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                lang = full_path.suffix.lstrip(".") or "text"
                return f"```{lang}\n{content}\n```"
            return match.group(0)

        return self._INCLUDE_RE.sub(_replace, text)

    # -- 标题锚点 { #id } --

    _ANCHOR_RE = re.compile(r"^(#{1,6}\s+.+?)\s*\{\s*#(\S+)\s*\}", re.MULTILINE)

    @staticmethod
    def _strip_heading_anchors(text: str) -> str:
        return MkDocsPreprocessor._ANCHOR_RE.sub(r"\1", text)
