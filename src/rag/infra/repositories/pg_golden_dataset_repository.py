import json

from rag.domain.entities.golden_record import GoldenRecord
from rag.domain.ports.golden_dataset_repository import GoldenDatasetRepositoryPort
from rag.infra.database.connection import get_pool

_SELECT = """SELECT id, project_id, query, ground_truth_chunks, reference_answer,
                     status, retrieved_chunk_ids, is_hit, hit_rank, evaluated_at,
                     created_at, updated_at, metadata"""


class PgGoldenDatasetRepository(GoldenDatasetRepositoryPort):
    """PostgreSQL 实现的黄金数据集仓储"""

    async def save(self, record: GoldenRecord) -> GoldenRecord:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""INSERT INTO golden_dataset (project_id, query, ground_truth_chunks, reference_answer, status, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING {_SELECT.replace('SELECT ', '')}""",
                _to_uuid(record.project_id),
                record.query,
                record.ground_truth_chunks,
                record.reference_answer,
                record.status,
                json.dumps(record.metadata) if record.metadata else "{}",
            )
        return _row_to_record(row)

    async def get_by_id(self, record_id: str) -> GoldenRecord | None:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"{_SELECT} FROM golden_dataset WHERE id = $1",
                _to_uuid(record_id),
            )
        if row is None:
            return None
        return _row_to_record(row)

    async def list_by_project(self, project_id: str) -> list[GoldenRecord]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"{_SELECT} FROM golden_dataset WHERE project_id = $1 ORDER BY created_at DESC",
                _to_uuid(project_id),
            )
        return [_row_to_record(row) for row in rows]

    async def list_by_project_and_status(
        self, project_id: str, status: str
    ) -> list[GoldenRecord]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"{_SELECT} FROM golden_dataset WHERE project_id = $1 AND status = $2 ORDER BY created_at DESC",
                _to_uuid(project_id),
                status,
            )
        return [_row_to_record(row) for row in rows]

    async def update(self, record: GoldenRecord) -> GoldenRecord:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""UPDATE golden_dataset
                   SET query = $1, ground_truth_chunks = $2, reference_answer = $3,
                       status = $4, retrieved_chunk_ids = $5, is_hit = $6, hit_rank = $7,
                       evaluated_at = $8, metadata = $9, updated_at = now()
                   WHERE id = $10
                   RETURNING {_SELECT.replace('SELECT ', '')}""",
                record.query,
                record.ground_truth_chunks,
                record.reference_answer,
                record.status,
                record.retrieved_chunk_ids,
                record.is_hit,
                record.hit_rank,
                record.evaluated_at,
                json.dumps(record.metadata) if record.metadata else "{}",
                _to_uuid(record.id),
            )
        if row is None:
            raise ValueError(f"黄金记录 {record.id} 不存在")
        return _row_to_record(row)

    async def delete(self, record_id: str) -> bool:
        pool = get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM golden_dataset WHERE id = $1",
                _to_uuid(record_id),
            )
            return result == "DELETE 1"

    async def update_status(self, record_id: str, status: str) -> GoldenRecord:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""UPDATE golden_dataset SET status = $1, updated_at = now() WHERE id = $2
                   RETURNING {_SELECT.replace('SELECT ', '')}""",
                status,
                _to_uuid(record_id),
            )
        if row is None:
            raise ValueError(f"黄金记录 {record_id} 不存在")
        return _row_to_record(row)

    async def batch_update_status(self, record_ids: list[str], status: str) -> int:
        if not record_ids:
            return 0
        pool = get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE golden_dataset SET status = $1, updated_at = now() WHERE id = ANY($2::uuid[])",
                status,
                record_ids,
            )
        # result 格式: "UPDATE N"
        count_str = result.split()[-1]
        return int(count_str)

    async def list_by_chunk_id(self, chunk_id: str, project_id: str) -> list[GoldenRecord]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""{_SELECT} FROM golden_dataset
                   WHERE project_id = $1 AND $2 = ANY(ground_truth_chunks)
                   ORDER BY created_at DESC""",
                _to_uuid(project_id),
                chunk_id,
            )
        return [_row_to_record(row) for row in rows]


def _to_uuid(value: str) -> str:
    return value


def _row_to_record(row) -> GoldenRecord:
    metadata_raw = row["metadata"]
    if isinstance(metadata_raw, str):
        metadata = json.loads(metadata_raw)
    elif isinstance(metadata_raw, dict):
        metadata = metadata_raw
    else:
        metadata = {}

    return GoldenRecord(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        query=row["query"],
        ground_truth_chunks=list(row["ground_truth_chunks"]) if row["ground_truth_chunks"] else [],
        reference_answer=row["reference_answer"] or "",
        status=row.get("status", "approved"),
        retrieved_chunk_ids=list(row["retrieved_chunk_ids"]) if row["retrieved_chunk_ids"] else [],
        is_hit=row["is_hit"],
        hit_rank=row["hit_rank"],
        evaluated_at=row["evaluated_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        metadata=metadata,
    )
