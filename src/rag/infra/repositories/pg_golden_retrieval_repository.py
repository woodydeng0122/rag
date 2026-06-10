from rag.domain.entities.golden_retrieval import GoldenRetrieval
from rag.domain.entities.golden_retrieval_item import GoldenRetrievalItem
from rag.domain.ports.golden_retrieval_repository import GoldenRetrievalRepositoryPort, RetrievalSummary
from rag.infra.repositories.base import BaseRepository, to_uuid, acquire_connection


class PgGoldenRetrievalRepository(GoldenRetrievalRepositoryPort, BaseRepository):
    """PostgreSQL 实现的黄金记录检索结果仓储"""

    async def save(self, retrieval: GoldenRetrieval, items: list[GoldenRetrievalItem]) -> GoldenRetrieval:
        async with acquire_connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    "DELETE FROM golden_retrieval WHERE golden_id = $1",
                    to_uuid(retrieval.golden_id),
                )
                row = await conn.fetchrow(
                    """INSERT INTO golden_retrieval (golden_id, max_k, latency_ms, embed_model_name, embed_latency_ms, search_latency_ms,
                       load_embeddings_latency_ms, load_project_latency_ms, load_embed_model_latency_ms, get_embedder_latency_ms, build_matrix_latency_ms)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    RETURNING id, golden_id, max_k, latency_ms, embed_model_name, embed_latency_ms, search_latency_ms,
                              load_embeddings_latency_ms, load_project_latency_ms, load_embed_model_latency_ms, get_embedder_latency_ms, build_matrix_latency_ms, created_at""",
                    to_uuid(retrieval.golden_id),
                    retrieval.max_k,
                    retrieval.latency_ms,
                    retrieval.embed_model_name,
                    retrieval.embed_latency_ms,
                    retrieval.search_latency_ms,
                    retrieval.load_embeddings_latency_ms,
                    retrieval.load_project_latency_ms,
                    retrieval.load_embed_model_latency_ms,
                    retrieval.get_embedder_latency_ms,
                    retrieval.build_matrix_latency_ms,
                )
                retrieval_id = str(row["id"])
                for item in items:
                    await conn.execute(
                        """INSERT INTO golden_retrieval_item (retrieval_id, chunk_id, score, rank)
                        VALUES ($1, $2, $3, $4)""",
                        to_uuid(retrieval_id),
                        item.chunk_id,
                        item.score,
                        item.rank,
                    )
        return _row_to_retrieval(row)

    async def get_by_golden_id(self, golden_id: str) -> tuple[GoldenRetrieval, list[GoldenRetrievalItem]] | None:
        async with acquire_connection() as conn:
            row = await conn.fetchrow(
                """SELECT id, golden_id, max_k, latency_ms, embed_model_name, embed_latency_ms, search_latency_ms,
                          load_embeddings_latency_ms, load_project_latency_ms, load_embed_model_latency_ms, get_embedder_latency_ms, build_matrix_latency_ms, created_at
                FROM golden_retrieval WHERE golden_id = $1""",
                to_uuid(golden_id),
            )
            if row is None:
                return None
            item_rows = await conn.fetch(
                """SELECT id, retrieval_id, chunk_id, score, rank
                FROM golden_retrieval_item WHERE retrieval_id = $1
                ORDER BY rank""",
                row["id"],
            )
        retrieval = _row_to_retrieval(row)
        items = [_row_to_item(r) for r in item_rows]
        return retrieval, items

    async def delete_by_golden_id(self, golden_id: str) -> bool:
        return await self._delete_by_id("golden_retrieval", golden_id, id_column="golden_id")

    async def exists_by_golden_id(self, golden_id: str) -> bool:
        row = await self._fetch_one(
            "SELECT 1 FROM golden_retrieval WHERE golden_id = $1",
            to_uuid(golden_id),
        )
        return row is not None

    async def exists_by_golden_ids(self, golden_ids: list[str]) -> set[str]:
        if not golden_ids:
            return set()
        rows = await self._fetch_all(
            "SELECT golden_id FROM golden_retrieval WHERE golden_id = ANY($1::uuid[])",
            golden_ids,
        )
        return {str(row["golden_id"]) for row in rows}

    async def get_retrieval_summaries(self, golden_ids: list[str]) -> dict[str, RetrievalSummary]:
        if not golden_ids:
            return {}
        rows = await self._fetch_all(
            """SELECT gr.golden_id,
                      COUNT(ri.chunk_id) FILTER (WHERE ri.chunk_id = ANY(g.ground_truth_chunks)) AS hit_count,
                      COALESCE(array_length(g.ground_truth_chunks, 1), 0) AS gt_total
               FROM golden_retrieval gr
               JOIN golden g ON g.id = gr.golden_id
               LEFT JOIN golden_retrieval_item ri ON ri.retrieval_id = gr.id
               WHERE gr.golden_id = ANY($1::uuid[])
               GROUP BY gr.golden_id, g.ground_truth_chunks""",
            golden_ids,
        )
        return {
            str(row["golden_id"]): RetrievalSummary(
                hit_count=row["hit_count"],
                gt_total=row["gt_total"],
            )
            for row in rows
        }

    async def list_by_project_with_items(self, project_id: str) -> list[tuple[GoldenRetrieval, list[GoldenRetrievalItem]]]:
        async with acquire_connection() as conn:
            retrieval_rows = await conn.fetch(
                """SELECT gr.id, gr.golden_id, gr.max_k, gr.latency_ms,
                          gr.embed_model_name, gr.embed_latency_ms, gr.search_latency_ms,
                          gr.load_embeddings_latency_ms, gr.load_project_latency_ms,
                          gr.load_embed_model_latency_ms, gr.get_embedder_latency_ms, gr.build_matrix_latency_ms, gr.created_at
                   FROM golden_retrieval gr
                   JOIN golden g ON g.id = gr.golden_id
                   WHERE g.project_id = $1""",
                project_id,
            )
            if not retrieval_rows:
                return []
            retrieval_ids = [row["id"] for row in retrieval_rows]
            item_rows = await conn.fetch(
                """SELECT id, retrieval_id, chunk_id, score, rank
                   FROM golden_retrieval_item
                   WHERE retrieval_id = ANY($1::uuid[])
                   ORDER BY rank""",
                retrieval_ids,
            )
        items_map: dict[str, list] = {}
        for ir in item_rows:
            rid = str(ir["retrieval_id"])
            items_map.setdefault(rid, []).append(_row_to_item(ir))
        return [
            (_row_to_retrieval(row), items_map.get(str(row["id"]), []))
            for row in retrieval_rows
        ]


def _row_to_retrieval(row) -> GoldenRetrieval:
    return GoldenRetrieval(
        id=str(row["id"]),
        golden_id=str(row["golden_id"]),
        max_k=row["max_k"],
        latency_ms=row["latency_ms"],
        embed_model_name=row["embed_model_name"] or "",
        embed_latency_ms=row.get("embed_latency_ms", 0) or 0,
        search_latency_ms=row.get("search_latency_ms", 0) or 0,
        load_embeddings_latency_ms=row.get("load_embeddings_latency_ms", 0) or 0,
        load_project_latency_ms=row.get("load_project_latency_ms", 0) or 0,
        load_embed_model_latency_ms=row.get("load_embed_model_latency_ms", 0) or 0,
        get_embedder_latency_ms=row.get("get_embedder_latency_ms", 0) or 0,
        build_matrix_latency_ms=row.get("build_matrix_latency_ms", 0) or 0,
        created_at=row["created_at"],
    )


def _row_to_item(row) -> GoldenRetrievalItem:
    return GoldenRetrievalItem(
        id=str(row["id"]),
        retrieval_id=str(row["retrieval_id"]),
        chunk_id=row["chunk_id"],
        score=float(row["score"]),
        rank=int(row["rank"]),
    )
