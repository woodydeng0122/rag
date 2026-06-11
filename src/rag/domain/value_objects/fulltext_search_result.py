from dataclasses import dataclass


@dataclass
class FulltextSearchResult:
    """全文检索结果项"""

    chunk_id: str
    score: float
