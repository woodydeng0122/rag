import re
from rag.domain.entities.chunk import Chunk
from rag.domain.ports.splitter import SplitterPort


class SectionHeadingSplitter(SplitterPort):
    """基于标题分节的分块策略实现"""

    def __init__(self, min_chars: int = 200, max_chars: int = 2000):
        self._min_chars = min_chars
        self._max_chars = max_chars

    def split(self, text: str, **kwargs) -> list[Chunk]:
        min_chars = kwargs.get("min_chars", self._min_chars)
        max_chars = kwargs.get("max_chars", self._max_chars)
        sections = self._split_by_heading(text, "## ")
        sections = self._merge_short_chunks(sections, min_chars)
        sections = self._resplit_long_chunks(sections, max_chars)
        sections = self._protect_code_blocks(sections, max_chars)
        return [
            Chunk(id="", content=sec["text"], heading=sec.get("heading", ""))
            for sec in sections
        ]

    @staticmethod
    def _split_by_heading(text: str, heading_prefix: str = "## ") -> list[dict]:
        parts = re.split(rf"^(?={re.escape(heading_prefix)})", text, flags=re.M)
        sections = []
        for part in parts:
            stripped = part.strip()
            if not stripped:
                continue
            first_line = stripped.split("\n", 1)[0]
            heading = first_line.replace(heading_prefix, "").strip() if first_line.startswith(heading_prefix) else ""
            sections.append({"heading": heading, "text": stripped})
        return sections

    @staticmethod
    def _merge_short_chunks(sections: list[dict], min_chars: int = 200) -> list[dict]:
        if not sections:
            return []
        merged = [sections[0].copy()]
        for sec in sections[1:]:
            if len(merged[-1]["text"]) < min_chars:
                merged[-1]["text"] += "\n\n" + sec["text"]
                if not merged[-1]["heading"] and sec["heading"]:
                    merged[-1]["heading"] = sec["heading"]
            else:
                merged.append(sec.copy())
        return merged

    def _resplit_long_chunks(self, sections: list[dict], max_chars: int = 2000) -> list[dict]:
        result = []
        for sec in sections:
            if len(sec["text"]) <= max_chars:
                result.append(sec)
                continue
            sub_sections = self._split_by_heading(sec["text"], "### ")
            if len(sub_sections) > 1:
                result.extend(sub_sections)
                continue
            if re.search(r"```[\s\S]*?```", sec["text"]):
                result.extend(self._split_preserving_code(sec, max_chars))
            else:
                result.extend(self._split_by_paragraphs(sec, max_chars))
        return result

    @staticmethod
    def _split_by_paragraphs(section: dict, max_chars: int) -> list[dict]:
        text = section["text"]
        heading = section["heading"]
        paragraphs = re.split(r"\n\n+", text)
        chunks = []
        current = ""
        for para in paragraphs:
            if not current:
                current = para
            elif len(current) + len(para) + 2 <= max_chars:
                current += "\n\n" + para
            else:
                chunks.append({"heading": heading, "text": current})
                current = para
        if current:
            chunks.append({"heading": heading, "text": current})
        return chunks

    def _protect_code_blocks(self, sections: list[dict], max_chars: int = 2000) -> list[dict]:
        result = []
        for sec in sections:
            if len(sec["text"]) <= max_chars:
                result.append(sec)
                continue
            code_blocks = re.findall(r"```[\s\S]*?```", sec["text"])
            if not code_blocks:
                result.extend(self._split_by_paragraphs(sec, max_chars))
                continue
            result.extend(self._split_preserving_code(sec, max_chars))
        return result

    @staticmethod
    def _split_preserving_code(section: dict, max_chars: int) -> list[dict]:
        text = section["text"]
        heading = section["heading"]
        parts = re.split(r"(```[\s\S]*?```)", text)
        chunks = []
        current = ""
        for part in parts:
            is_code = part.startswith("```") and part.endswith("```")
            if is_code:
                if len(current) + len(part) + 2 <= max_chars:
                    current += "\n" + part if current else part
                else:
                    if current:
                        chunks.append({"heading": heading, "text": current})
                    if len(part) > max_chars:
                        chunks.append({"heading": heading, "text": part})
                    else:
                        current = part
            else:
                stripped = part.strip()
                if not stripped:
                    continue
                if len(current) + len(stripped) + 2 <= max_chars:
                    current += "\n\n" + stripped if current else stripped
                else:
                    if current:
                        chunks.append({"heading": heading, "text": current})
                    current = stripped
        if current:
            chunks.append({"heading": heading, "text": current})
        return chunks
