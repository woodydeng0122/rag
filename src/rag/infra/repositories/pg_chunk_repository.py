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


class PgChunkRepository(ChunkRepositoryPort):
    """PostgreSQL 实现的分块仓储"""

    async def save_batch(self, chunks: list[Chunk], document_id: str = "") -> None:
        if not chunks:
            return
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.executemany(
                """INSERT INTO chunk (id, document_id, content, index, heading, source_file, search_tokens)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET content = $3, heading = $5, search_tokens = $7""",
                [
                    (c.id, _to_uuid(document_id), c.content, c.index, c.heading, c.source_file, _tokenize(c.content))
                    for c in chunks
                ],
            )

    async def list_by_document(self, document_id: str) -> list[Chunk]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, document_id, content, index, heading, source_file FROM chunk WHERE document_id = $1 ORDER BY index",
                _to_uuid(document_id),
            )
        return [_row_to_chunk(row) for row in rows]

    async def list_by_project(self, project_id: str, limit: int = 20, offset: int = 0) -> list[Chunk]:
        """按项目查询分块（跨文档），支持分页"""
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT c.id, c.content, c.index, c.heading, c.source_file
                   FROM chunk c
                   JOIN document d ON c.document_id = d.id
                   WHERE d.project_id = $1
                   ORDER BY c.created_at DESC
                   LIMIT $2 OFFSET $3""",
                _to_uuid(project_id),
                limit,
                offset,
            )
        return [_row_to_chunk(row) for row in rows]

    async def search_by_project(self, project_id: str, query: str, limit: int = 20, offset: int = 0) -> list[Chunk]:
        """按项目搜索分块内容，支持分页"""
        pool = get_pool()
        async with pool.acquire() as conn:
            if query:
                rows = await conn.fetch(
                    """SELECT c.id, c.content, c.index, c.heading, c.source_file
                       FROM chunk c
                       JOIN document d ON c.document_id = d.id
                       WHERE d.project_id = $1 AND c.content ILIKE $2
                       ORDER BY c.created_at DESC
                       LIMIT $3 OFFSET $4""",
                    _to_uuid(project_id),
                    f"%{query}%",
                    limit,
                    offset,
                )
            else:
                rows = await conn.fetch(
                    """SELECT c.id, c.content, c.index, c.heading, c.source_file
                       FROM chunk c
                       JOIN document d ON c.document_id = d.id
                       WHERE d.project_id = $1
                       ORDER BY c.created_at DESC
                       LIMIT $2 OFFSET $3""",
                    _to_uuid(project_id),
                    limit,
                    offset,
                )
        return [_row_to_chunk(row) for row in rows]

    async def get_by_ids(self, chunk_ids: list[str]) -> list[Chunk]:
        """按 ID 列表批量查询 chunk"""
        if not chunk_ids:
            return []
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT id, content, index, heading, source_file
                   FROM chunk WHERE id = ANY($1::varchar[])""",
                chunk_ids,
            )
        return [_row_to_chunk(row) for row in rows]

    async def get_by_ids_with_file_type(self, chunk_ids: list[str]) -> list[tuple[Chunk, str]]:
        """按 ID 列表批量查询 chunk，同时返回所属文档的 file_type"""
        if not chunk_ids:
            return []
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT c.id, c.content, c.index, c.heading, c.source_file,
                          d.file_type AS document_file_type
                   FROM chunk c
                   JOIN document d ON c.document_id = d.id
                   WHERE c.id = ANY($1::varchar[])""",
                chunk_ids,
            )
        return [(_row_to_chunk(row), row["document_file_type"]) for row in rows]

    async def count_by_project(self, project_id: str) -> int:
        """统计项目下的分块总数"""
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT COUNT(*) AS cnt FROM chunk c
                   JOIN document d ON c.document_id = d.id
                   WHERE d.project_id = $1""",
                _to_uuid(project_id),
            )
        return row["cnt"] if row else 0

    async def search_fulltext(self, project_id: str, query: str, top_k: int = 10) -> list[FulltextSearchResult]:
        """全文检索 — jieba 分词 + OR tsquery + ts_rank_cd 排序"""
        tsquery_str = _build_or_tsquery(query)
        if not tsquery_str:
            return []
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT c.id AS chunk_id,
                          ts_rank_cd(c.search_vector, to_tsquery('simple', $1)) AS score
                   FROM chunk c
                   JOIN document d ON c.document_id = d.id
                   WHERE d.project_id = $2
                     AND c.search_vector @@ to_tsquery('simple', $1)
                   ORDER BY score DESC
                   LIMIT $3""",
                tsquery_str,
                _to_uuid(project_id),
                top_k,
            )
        return [FulltextSearchResult(chunk_id=row["chunk_id"], score=float(row["score"])) for row in rows]


def _to_uuid(value: str) -> str:
    return value


def _row_to_chunk(row) -> Chunk:
    return Chunk(
        id=row["id"],
        content=row["content"],
        index=row["index"],
        source_file=row["source_file"],
        heading=row["heading"],
    )