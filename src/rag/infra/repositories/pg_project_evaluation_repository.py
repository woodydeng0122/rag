from rag.domain.entities.project_evaluation import ProjectEvaluation
from rag.domain.ports.project_evaluation_repository import ProjectEvaluationRepositoryPort
from rag.infra.database.connection import get_pool


class PgProjectEvaluationRepository(ProjectEvaluationRepositoryPort):
    """PostgreSQL 实现的项目评估统计仓储"""

    async def save(self, evaluation: ProjectEvaluation) -> ProjectEvaluation:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO project_evaluation
                (project_id, top_k, golden_total, golden_retrieved,
                 recall_at_k, mrr, hit_rate, full_hit_count, zero_hit_count,
                 avg_latency_ms, avg_embed_latency_ms, avg_search_latency_ms,
                 embed_model_name, remark)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING id, project_id, top_k, golden_total, golden_retrieved,
                          recall_at_k, mrr, hit_rate, full_hit_count, zero_hit_count,
                          avg_latency_ms, avg_embed_latency_ms, avg_search_latency_ms,
                          embed_model_name, remark, created_at""",
                evaluation.project_id,
                evaluation.top_k,
                evaluation.golden_total,
                evaluation.golden_retrieved,
                evaluation.recall_at_k,
                evaluation.mrr,
                evaluation.hit_rate,
                evaluation.full_hit_count,
                evaluation.zero_hit_count,
                evaluation.avg_latency_ms,
                evaluation.avg_embed_latency_ms,
                evaluation.avg_search_latency_ms,
                evaluation.embed_model_name,
                evaluation.remark,
            )
        return _row_to_evaluation(row)

    async def list_by_project(self, project_id: str) -> list[ProjectEvaluation]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT id, project_id, top_k, golden_total, golden_retrieved,
                          recall_at_k, mrr, hit_rate, full_hit_count, zero_hit_count,
                          avg_latency_ms, avg_embed_latency_ms, avg_search_latency_ms,
                          embed_model_name, remark, created_at
                   FROM project_evaluation
                   WHERE project_id = $1
                   ORDER BY created_at DESC""",
                project_id,
            )
        return [_row_to_evaluation(row) for row in rows]


    async def delete(self, evaluation_id: str) -> bool:
        pool = get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM project_evaluation WHERE id = $1",
                evaluation_id,
            )
        return result == "DELETE 1"

    async def update_remark(self, evaluation_id: str, remark: str) -> bool:
        pool = get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE project_evaluation SET remark = $1 WHERE id = $2",
                remark,
                evaluation_id,
            )
        return result == "UPDATE 1"


def _row_to_evaluation(row) -> ProjectEvaluation:
    return ProjectEvaluation(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        top_k=row["top_k"],
        golden_total=row["golden_total"],
        golden_retrieved=row["golden_retrieved"],
        recall_at_k=float(row["recall_at_k"]),
        mrr=float(row["mrr"]),
        hit_rate=float(row["hit_rate"]),
        full_hit_count=row["full_hit_count"],
        zero_hit_count=row["zero_hit_count"],
        avg_latency_ms=float(row["avg_latency_ms"]),
        avg_embed_latency_ms=float(row["avg_embed_latency_ms"]),
        avg_search_latency_ms=float(row["avg_search_latency_ms"]),
        embed_model_name=row["embed_model_name"] or "",
        remark=row["remark"] or "",
        created_at=row["created_at"],
    )
