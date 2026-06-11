import re
import unicodedata

import jieba

from rag.domain.entities.chunk import Chunk
from rag.domain.value_objects.fulltext_search_result import FulltextSearchResult
from rag.domain.ports.chunk_repository import ChunkRepositoryPort
from rag.infra.database.connection import get_pool


def _extract_english_words(text: str) -> list[str]:
    """从文本中提取英文词序列，转小写，去重"""
    # 提取连续英文字母序列，转小写
    words = re.findall(r"[A-Za-z]{2,}", text)
    seen = set()
    result = []
    for w in words:
        lw = w.lower()
        if lw not in seen:
            seen.add(lw)
            result.append(lw)
    return result


def _tokenize(text: str) -> str:
    """混合分词：jieba 分中文 + 提取英文词（小写）+ 标点分割词

    存储格式示例：FastAPI 扩展 → fastapi 扩展
    """
    english_words = _extract_english_words(text)
    # jieba 对纯英文序列不分割，整体作为一个 token，用英文提取补充分词
    chinese_tokens = [t for t in jieba.cut(text) if t.strip() and not re.match(r"^[A-Za-z]{2,}$", t)]
    all_tokens = english_words + chinese_tokens
    return " ".join(all_tokens)


def _build_or_tsquery(text: str) -> str:
    """构建 OR 连接的 tsquery — 提取英文词 + jieba 分词，任一词命中即召回"""
    english_words = _extract_english_words(text)
    chinese_tokens = jieba.cut(text)
    # 过滤掉纯英文词（已单独提取）和短token/标点
    chinese_terms = [
        t.strip() for t in chinese_tokens
        if t.strip() and len(t.strip()) > 1 and not re.match(r"^[A-Za-z]{2,}$", t)
    ]
    all_terms = english_words + chinese_terms
    if not all_terms:
        # 回退：用所有非空 token
        all_terms = [t.strip() for t in jieba.cut(text) if t.strip()]
    return " | ".join(all_terms)