import json

from rag.domain.entities.golden_record import GoldenRecord, GoldenStatus
from rag.domain.ports.golden_repository import GoldenRepositoryPort
from rag.infra.repositories.base import BaseRepository, to_uuid, acquire_connection

_SELECT = """SELECT id, project_id, query, ground_truth_chunks, reference_answer,
                     status, created_at, updated_at, metadata"""


class PgGoldenRepository(GoldenRepositoryPort, BaseRepository):
    """PostgreSQL 实现的黄金记录仓储"""

    async def save(self, record: GoldenRecord) -> GoldenRecord:
        row = await self._fetch_one(
            f"""INSERT INTO golden (project_id, query, ground_truth_chunks, reference_answer, status, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING {_SELECT.replace('SELECT ', '')}""",
            to_uuid(record.project_id),
            record.query,
            record.ground_truth_chunks,
            record.reference_answer,
            record.status.value,
            json.dumps(record.metadata) if record.metadata else "{}",
        )
        return _row_to_record(row)

    async def get_by_id(self, record_id: str) -> GoldenRecord | None:
        row = await self._fetch_one(
            f"{_SELECT} FROM golden WHERE id = $1",
            to_uuid(record_id),
        )
        if row is None:
            return None
        return _row_to_record(row)

    async def list_by_project(self, project_id: str) -> list[GoldenRecord]:
        rows = await self._fetch_all(
            f"{_SELECT} FROM golden WHERE project_id = $1 ORDER BY created_at DESC",
            to_uuid(project_id),
        )
        return [_row_to_record(row) for row in rows]

    async def list_by_project_and_status(
        self, project_id: str, status: GoldenStatus
    ) -> list[GoldenRecord]:
        rows = await self._fetch_all(
            f"{_SELECT} FROM golden WHERE project_id = $1 AND status = $2 ORDER BY created_at DESC",
            to_uuid(project_id),
            status.value,
        )
        return [_row_to_record(row) for row in rows]

    async def update(self, record: GoldenRecord) -> GoldenRecord:
        row = await self._fetch_one(
            f"""UPDATE golden
               SET query = $1, ground_truth_chunks = $2, reference_answer = $3,
                   status = $4, metadata = $5, updated_at = now()
               WHERE id = $6
               RETURNING {_SELECT.replace('SELECT ', '')}""",
            record.query,
            record.ground_truth_chunks,
            record.reference_answer,
            record.status.value,
            json.dumps(record.metadata) if record.metadata else "{}",
            to_uuid(record.id),
        )
        if row is None:
            raise ValueError(f"黄金记录 {record.id} 不存在")
        return _row_to_record(row)

    async def delete(self, record_id: str) -> bool:
        return await self._delete_by_id("golden", record_id)

    async def update_status(self, record_id: str, status: GoldenStatus) -> GoldenRecord:
        row = await self._fetch_one(
            f"""UPDATE golden SET status = $1, updated_at = now() WHERE id = $2
               RETURNING {_SELECT.replace('SELECT ', '')}""",
            status.value,
            to_uuid(record_id),
        )
        if row is None:
            raise ValueError(f"黄金记录 {record_id} 不存在")
        return _row_to_record(row)

    async def batch_update_status(self, record_ids: list[str], status: GoldenStatus) -> int:
        if not record_ids:
            return 0
        result = await self._execute(
            "UPDATE golden SET status = $1, updated_at = now() WHERE id = ANY($2::uuid[])",
            status.value,
            record_ids,
        )
        count_str = result.split()[-1]
        return int(count_str)

    async def list_by_chunk_id(self, chunk_id: str, project_id: str) -> list[GoldenRecord]:
        rows = await self._fetch_all(
            f"""{_SELECT} FROM golden
               WHERE project_id = $1 AND $2 = ANY(ground_truth_chunks)
               ORDER BY created_at DESC""",
            to_uuid(project_id),
            chunk_id,
        )
        return [_row_to_record(row) for row in rows]

    async def count_by_document_ids(self, document_ids: list[str]) -> dict[str, int]:
        """按文档 ID 批量统计关联的黄金记录条数"""
        if not document_ids:
            return {}
        rows = await self._fetch_all(
            """SELECT c.document_id, COUNT(DISTINCT gd.id) AS golden_count
               FROM golden gd
               JOIN chunk c ON c.id = ANY(gd.ground_truth_chunks)
               WHERE c.document_id = ANY($1::uuid[])
               GROUP BY c.document_id""",
            document_ids,
        )
        return {str(row["document_id"]): row["golden_count"] for row in rows}

    async def list_by_retrieval_status(
        self, project_id: str, retrieval_status: str
    ) -> list[GoldenRecord]:
        _SEL = """SELECT g.id, g.project_id, g.query, g.ground_truth_chunks, g.reference_answer,
                         g.status, g.created_at, g.updated_at, g.metadata"""
        async with acquire_connection() as conn:
            if retrieval_status == "hit":
                rows = await conn.fetch(
                    f"""{_SEL} FROM golden g
                       JOIN golden_retrieval gr ON gr.golden_id = g.id
                       JOIN golden_retrieval_item gri ON gri.retrieval_id = gr.id
                       WHERE g.project_id = $1 AND gri.chunk_id = ANY(g.ground_truth_chunks)
                       GROUP BY g.id
                       ORDER BY g.created_at DESC""",
                    to_uuid(project_id),
                )
            elif retrieval_status == "miss":
                rows = await conn.fetch(
                    f"""{_SEL} FROM golden g
                       JOIN golden_retrieval gr ON gr.golden_id = g.id
                       WHERE g.project_id = $1
                       AND NOT EXISTS (
                           SELECT 1 FROM golden_retrieval_item gri
                           WHERE gri.retrieval_id = gr.id
                           AND gri.chunk_id = ANY(g.ground_truth_chunks)
                       )
                       ORDER BY g.created_at DESC""",
                    to_uuid(project_id),
                )
            elif retrieval_status == "unretrieved":
                rows = await conn.fetch(
                    f"""{_SEL} FROM golden g
                       WHERE g.project_id = $1
                       AND NOT EXISTS (
                           SELECT 1 FROM golden_retrieval gr WHERE gr.golden_id = g.id
                       )
                       ORDER BY g.created_at DESC""",
                    to_uuid(project_id),
                )
            else:
                rows = []
        return [_row_to_record(row) for row in rows]

    async def list_by_document(self, project_id: str, document_id: str) -> list[GoldenRecord]:
        """按文档 ID 查询关联的黄金记录"""
        rows = await self._fetch_all(
            f"""{_SELECT} FROM golden gd
               JOIN chunk c ON c.id = ANY(gd.ground_truth_chunks)
               WHERE gd.project_id = $1 AND c.document_id = $2
               ORDER BY gd.created_at DESC""",
            to_uuid(project_id),
            to_uuid(document_id),
        )
        return [_row_to_record(row) for row in rows]


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
        status=GoldenStatus(row.get("status", "approved")),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        metadata=metadata,
    )
