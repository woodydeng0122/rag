import json

from rag.domain.entities.golden_record import GoldenRecord
from rag.domain.ports.golden_dataset_repository import GoldenDatasetRepositoryPort
from rag.infra.database.connection import get_pool

_SELECT = """SELECT id, project_id, query, ground_truth_chunks, reference_answer,
                     retrieved_chunk_ids, is_hit, hit_rank, evaluated_at, created_at, metadata"""


class PgGoldenDatasetRepository(GoldenDatasetRepositoryPort):
    """PostgreSQL 实现的黄金数据集仓储"""

    async def save(self, record: GoldenRecord) -> GoldenRecord:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""INSERT INTO golden_dataset (project_id, query, ground_truth_chunks, reference_answer, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING {_SELECT.replace('SELECT ', '')}""",
                _to_uuid(record.project_id),
                record.query,
                record.ground_truth_chunks,
                record.reference_answer,
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

    async def update(self, record: GoldenRecord) -> GoldenRecord:
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""UPDATE golden_dataset
                   SET query = $1, ground_truth_chunks = $2, reference_answer = $3,
                       retrieved_chunk_ids = $4, is_hit = $5, hit_rank = $6, evaluated_at = $7,
                       metadata = $8
                   WHERE id = $9
                   RETURNING {_SELECT.replace('SELECT ', '')}""",
                record.query,
                record.ground_truth_chunks,
                record.reference_answer,
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
        retrieved_chunk_ids=list(row["retrieved_chunk_ids"]) if row["retrieved_chunk_ids"] else [],
        is_hit=row["is_hit"],
        hit_rank=row["hit_rank"],
        evaluated_at=row["evaluated_at"],
        created_at=row["created_at"],
        metadata=metadata,
    )
