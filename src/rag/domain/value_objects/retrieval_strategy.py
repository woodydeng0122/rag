from enum import Enum


class RetrievalStrategy(str, Enum):
    """检索策略枚举"""

    COSINE = "cosine"          # 内存余弦相似度（暴力搜索）
    VECTOR = "vector"          # pgvector 精确余弦距离
    BM25 = "bm25"              # PostgreSQL 全文检索
    HYBRID = "hybrid"          # Vector + BM25 双路召回 + RRF 融合
