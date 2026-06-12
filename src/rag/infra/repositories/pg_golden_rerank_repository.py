from rag.domain.entities.golden_rerank import GoldenRerank
from rag.domain.entities.golden_rerank_item import GoldenRerankItem
from rag.domain.ports.golden_rerank_repository import GoldenRerankRepositoryPort, RerankSummary
from rag.infra.repositories.base import BaseRepository, to_uuid, acquire_connection


class PgGoldenRerankRepository(GoldenRerankRepositoryPort, BaseRepository):
    """PostgreSQL 实现的黄金记录重排结果仓储"""

    async def save(self, rerank: GoldenRerank, items: list[GoldenRerankItem]) -> GoldenRerank:
        async with acquire_connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    "DELETE FROM golden_rerank WHERE golden_id = $1",
                    to_uuid(rerank.golden_id),
                )
                row = await conn.fetchrow(
                    """INSERT INTO golden_rerank (golden_id, top_k, latency_ms, model_name)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id, golden_id, top_k, latency_ms, model_name, created_at""",
                    to_uuid(rerank.golden_id),
                    rerank.top_k,
                    rerank.latency_ms,
                    rerank.model_name,
                )
                rerank_id = str(row["id"])
                for item in items:
                    await conn.execute(
                        """INSERT INTO golden_rerank_item (rerank_id, chunk_id, original_rank, rerank_score, rerank_rank)
                        VALUES ($1, $2, $3, $4, $5)""",
                        to_uuid(rerank_id),
                        item.chunk_id,
                        item.original_rank,
                        item.rerank_score,
                        item.rerank_rank,
                    )
        return _row_to_rerank(row)

    async def get_by_golden_id(self, golden_id: str) -> tuple[GoldenRerank, list[GoldenRerankItem]] | None:
        async with acquire_connection() as conn:
            row = await conn.fetchrow(
                """SELECT id, golden_id, top_k, latency_ms, model_name, created_at
                FROM golden_rerank WHERE golden_id = $1""",
                to_uuid(golden_id),
            )
            if row is None:
                return None
            item_rows = await conn.fetch(
                """SELECT id, rerank_id, chunk_id, original_rank, rerank_score, rerank_rank
                FROM golden_rerank_item WHERE rerank_id = $1
                ORDER BY rerank_rank""",
                row["id"],
            )
        rerank = _row_to_rerank(row)
        items = [_row_to_item(r) for r in item_rows]
        return rerank, items

    async def delete_by_golden_id(self, golden_id: str) -> bool:
        return await self._delete_by_id("golden_rerank", golden_id, id_column="golden_id")

    async def exists_by_golden_ids(self, golden_ids: list[str]) -> set[str]:
        if not golden_ids:
            return set()
        rows = await self._fetch_all(
            "SELECT golden_id FROM golden_rerank WHERE golden_id = ANY($1::uuid[])",
            golden_ids,
        )
        return {str(row["golden_id"]) for row in rows}

    async def get_rerank_summaries(self, golden_ids: list[str]) -> dict[str, RerankSummary]:
        if not golden_ids:
            return {}
        rows = await self._fetch_all(
            """SELECT gr_rk.golden_id,
                      COUNT(ri.chunk_id) FILTER (WHERE ri.chunk_id = ANY(g.ground_truth_chunks)) AS hit_count,
                      COALESCE(array_length(g.ground_truth_chunks, 1), 0) AS gt_total,
                      COALESCE(ARRAY_AGG(ri.rerank_rank) FILTER (WHERE ri.chunk_id = ANY(g.ground_truth_chunks)), '{}') AS hit_ranks
               FROM golden_rerank gr_rk
               JOIN golden g ON g.id = gr_rk.golden_id
               LEFT JOIN golden_rerank_item ri ON ri.rerank_id = gr_rk.id
               WHERE gr_rk.golden_id = ANY($1::uuid[])
               GROUP BY gr_rk.golden_id, g.ground_truth_chunks""",
            golden_ids,
        )
        return {
            str(row["golden_id"]): RerankSummary(
                hit_count=row["hit_count"],
                gt_total=row["gt_total"],
                hit_ranks=sorted(row["hit_ranks"]) if row["hit_ranks"] else [],
            )
            for row in rows
        }


def _row_to_rerank(row) -> GoldenRerank:
    return GoldenRerank(
        id=str(row["id"]),
        golden_id=str(row["golden_id"]),
        top_k=row["top_k"],
        latency_ms=row["latency_ms"],
        model_name=row["model_name"] or "",
        created_at=row["created_at"],
    )


def _row_to_item(row) -> GoldenRerankItem:
    return GoldenRerankItem(
        id=str(row["id"]),
        rerank_id=str(row["rerank_id"]),
        chunk_id=row["chunk_id"],
        original_rank=int(row["original_rank"]),
        rerank_score=float(row["rerank_score"]),
        rerank_rank=int(row["rerank_rank"]),
    )
