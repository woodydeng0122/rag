import json

from rag.domain.entities.generate_config import GenerateConfig
from rag.domain.entities.generation_task import GenerationTask, TaskStatus
from rag.domain.ports.generation_task_repository import GenerationTaskRepositoryPort
from rag.infra.database.connection import get_pool

_SELECT = """SELECT id, project_id, status, total, completed, failed,
                     document_ids, chunk_ids, config, error_message,
                     created_at, updated_at, finished_at"""


class PgGenerationTaskRepository(GenerationTaskRepositoryPort):
    """PostgreSQL 实现的生成任务仓储"""

    async def save(self, task: GenerationTask) -> GenerationTask:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""INSERT INTO generation_task
                    (project_id, status, total, completed, failed,
                     document_ids, chunk_ids, config, error_message)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING {_SELECT.replace('SELECT ', '')}""",
                _to_uuid(task.project_id),
                task.status.value,
                task.total,
                task.completed,
                task.failed,
                task.document_ids,
                task.chunk_ids,
                _config_to_json(task.config),
                task.error_message,
            )
        return _row_to_task(row)

    async def get_by_id(self, task_id: str) -> GenerationTask | None:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"{_SELECT} FROM generation_task WHERE id = $1",
                _to_uuid(task_id),
            )
        if row is None:
            return None
        return _row_to_task(row)

    async def list_by_project(self, project_id: str) -> list[GenerationTask]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"{_SELECT} FROM generation_task WHERE project_id = $1 ORDER BY created_at DESC",
                _to_uuid(project_id),
            )
        return [_row_to_task(row) for row in rows]

    async def update(self, task: GenerationTask) -> GenerationTask:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""UPDATE generation_task
                   SET status = $1, total = $2, completed = $3, failed = $4,
                       document_ids = $5, chunk_ids = $6, config = $7,
                       error_message = $8, finished_at = $9
                   WHERE id = $10
                   RETURNING {_SELECT.replace('SELECT ', '')}""",
                task.status.value,
                task.total,
                task.completed,
                task.failed,
                task.document_ids,
                task.chunk_ids,
                _config_to_json(task.config),
                task.error_message,
                task.finished_at,
                _to_uuid(task.id),
            )
        if row is None:
            raise ValueError(f"生成任务 {task.id} 不存在")
        return _row_to_task(row)


def _to_uuid(value: str) -> str:
    return value


def _config_to_json(config: GenerateConfig | None) -> str:
    """将 GenerateConfig 序列化为 JSON 字符串"""
    if config is None:
        return "{}"
    return json.dumps(config.to_dict())


def _row_to_task(row) -> GenerationTask:
    config_raw = row["config"]
    if isinstance(config_raw, str):
        config = GenerateConfig.from_dict(json.loads(config_raw))
    elif isinstance(config_raw, dict):
        config = GenerateConfig.from_dict(config_raw)
    else:
        config = None

    return GenerationTask.reconstruct(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        status=TaskStatus(row["status"]),
        total=row["total"],
        completed=row["completed"],
        failed=row["failed"],
        document_ids=list(row["document_ids"]) if row["document_ids"] else [],
        chunk_ids=list(row["chunk_ids"]) if row["chunk_ids"] else [],
        config=config,
        error_message=row["error_message"] or "",
        created_at=row["created_at"],
        updated_at=row.get("updated_at"),
        finished_at=row["finished_at"],
    )
