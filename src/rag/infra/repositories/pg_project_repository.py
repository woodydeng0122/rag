from datetime import datetime

from rag.domain.entities.project import Project
from rag.domain.value_objects.project_eval_summary import ProjectEvalSummary
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.infra.database.connection import get_pool


class PgProjectRepository(ProjectRepositoryPort):
    """PostgreSQL 实现的项目仓储"""

    _SELECT = """SELECT id, name, description, embed_model_id, embed_dimension,
                        created_at, updated_at,
                        eval_recall_at_10, eval_mrr, eval_answerable, eval_total,
                        eval_latency_avg_ms, evaluated_at
                 FROM project"""

    async def save(self, project: Project) -> Project:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO project (name, description, embed_model_id, embed_dimension)
                VALUES ($1, $2, $3, $4)
                RETURNING id, name, description, embed_model_id, embed_dimension,
                          created_at, updated_at,
                          eval_recall_at_10, eval_mrr, eval_answerable, eval_total,
                          eval_latency_avg_ms, evaluated_at""",
                project.name,
                project.description,
                _to_uuid(project.embed_model_id) if project.embed_model_id else None,
                project.embed_dimension,
            )
        return _row_to_project(row)

    async def get_by_id(self, project_id: str) -> Project | None:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"{self._SELECT} WHERE id = $1",
                _to_uuid(project_id),
            )
        if row is None:
            return None
        return _row_to_project(row)

    async def list(self) -> list[Project]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"{self._SELECT} ORDER BY created_at DESC"
            )
        return [_row_to_project(row) for row in rows]

    async def update(self, project: Project) -> Project:
        pool = get_pool()
        async with pool.acquire() as conn:
            eval_s = project.eval_summary
            row = await conn.fetchrow(
                """UPDATE project SET name = $1, description = $2, updated_at = now(),
                      eval_recall_at_10 = $3, eval_mrr = $4, eval_answerable = $5,
                      eval_total = $6, eval_latency_avg_ms = $7, evaluated_at = $8
                WHERE id = $9
                RETURNING id, name, description, embed_model_id, embed_dimension,
                          created_at, updated_at,
                          eval_recall_at_10, eval_mrr, eval_answerable, eval_total,
                          eval_latency_avg_ms, evaluated_at""",
                project.name,
                project.description,
                eval_s.recall_at_10 if eval_s else None,
                eval_s.mrr if eval_s else None,
                eval_s.answerable if eval_s else None,
                eval_s.total if eval_s else None,
                eval_s.latency_avg_ms if eval_s else None,
                eval_s.evaluated_at if eval_s else None,
                _to_uuid(project.id),
            )
        if row is None:
            raise ValueError(f"项目 {project.id} 不存在")
        return _row_to_project(row)

    async def delete(self, project_id: str) -> bool:
        pool = get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM project WHERE id = $1",
                _to_uuid(project_id),
            )
        return result == "DELETE 1"


def _to_uuid(value: str) -> str:
    """确保值是合法的 UUID 字符串，asyncpg 会自动转换"""
    return value


def _row_to_project(row) -> Project:
    embed_model_id = row["embed_model_id"]
    # 构建评测汇总（任一字段非空即视为有评测数据）
    eval_summary = None
    if row["eval_recall_at_10"] is not None or row["eval_mrr"] is not None:
        eval_summary = ProjectEvalSummary(
            recall_at_10=row["eval_recall_at_10"],
            mrr=row["eval_mrr"],
            answerable=row["eval_answerable"],
            total=row["eval_total"],
            latency_avg_ms=row["eval_latency_avg_ms"],
            evaluated_at=row["evaluated_at"],
        )
    return Project(
        id=str(row["id"]),
        name=row["name"],
        description=row["description"] or "",
        embed_model_id=str(embed_model_id) if embed_model_id else "",
        embed_dimension=row["embed_dimension"] or 512,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        eval_summary=eval_summary,
    )
