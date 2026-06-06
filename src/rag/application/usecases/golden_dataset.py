from dataclasses import dataclass, field

from rag.domain.entities.golden_record import GoldenRecord
from rag.domain.ports.golden_dataset_repository import GoldenDatasetRepositoryPort
from rag.domain.ports.chunk_repository import ChunkRepositoryPort


@dataclass
class SkippedRecord:
    """跳过的记录"""
    row: int
    reason: str


@dataclass
class ImportResult:
    """导入结果"""
    success_count: int = 0
    skipped_count: int = 0
    skipped: list[SkippedRecord] = field(default_factory=list)


class GoldenDatasetUseCase:
    """黄金数据集 CRUD + 导入用例"""

    def __init__(self, golden_repo: GoldenDatasetRepositoryPort, chunk_repo: ChunkRepositoryPort):
        self.golden_repo = golden_repo
        self.chunk_repo = chunk_repo

    async def create(self, project_id: str, query: str, ground_truth_chunks: list[str], reference_answer: str = "", metadata: dict | None = None) -> GoldenRecord:
        record = GoldenRecord(
            project_id=project_id,
            query=query,
            ground_truth_chunks=ground_truth_chunks,
            reference_answer=reference_answer,
            metadata=metadata or {},
        )
        return await self.golden_repo.save(record)

    async def get(self, record_id: str) -> GoldenRecord | None:
        return await self.golden_repo.get_by_id(record_id)

    async def list_by_project(self, project_id: str, status: str | None = None) -> list[GoldenRecord]:
        if status:
            return await self.golden_repo.list_by_project_and_status(project_id, status)
        return await self.golden_repo.list_by_project(project_id)

    async def update(self, record_id: str, query: str, ground_truth_chunks: list[str], reference_answer: str = "", status: str | None = None) -> GoldenRecord:
        record = await self.golden_repo.get_by_id(record_id)
        if record is None:
            raise ValueError(f"黄金记录 {record_id} 不存在")
        record.query = query
        record.ground_truth_chunks = ground_truth_chunks
        record.reference_answer = reference_answer
        if status is not None:
            record.status = status
        return await self.golden_repo.update(record)

    async def delete(self, record_id: str) -> bool:
        return await self.golden_repo.delete(record_id)

    async def approve(self, record_id: str) -> GoldenRecord:
        """审批通过单条记录"""
        return await self.golden_repo.update_status(record_id, "approved")

    async def reject(self, record_id: str) -> GoldenRecord:
        """拒绝单条记录"""
        return await self.golden_repo.update_status(record_id, "rejected")

    async def batch_approve(self, record_ids: list[str]) -> int:
        """批量审批通过"""
        return await self.golden_repo.batch_update_status(record_ids, "approved")

    async def batch_reject(self, record_ids: list[str]) -> int:
        """批量拒绝"""
        return await self.golden_repo.batch_update_status(record_ids, "rejected")

    async def list_by_chunk_id(self, chunk_id: str, project_id: str) -> list[GoldenRecord]:
        """查询分块关联的黄金记录"""
        return await self.golden_repo.list_by_chunk_id(chunk_id, project_id)

    async def import_records(self, project_id: str, records: list[dict]) -> ImportResult:
        """批量导入黄金记录，严格校验 chunk ID"""
        # 一次性加载项目所有 chunk ID，用于 O(1) 校验
        all_chunks = await self.chunk_repo.list_by_project(project_id, limit=10000, offset=0)
        valid_chunk_ids = {c.id for c in all_chunks}

        result = ImportResult()

        for i, raw in enumerate(records, start=1):
            query = raw.get("query", "").strip()
            gt_chunks = raw.get("ground_truth_chunks", [])
            ref_answer = raw.get("reference_answer", "")
            metadata = raw.get("metadata", {})

            # 校验必填字段
            if not query:
                result.skipped_count += 1
                result.skipped.append(SkippedRecord(row=i, reason="query 不能为空"))
                continue

            if not gt_chunks:
                result.skipped_count += 1
                result.skipped.append(SkippedRecord(row=i, reason="ground_truth_chunks 不能为空"))
                continue

            # 严格校验 chunk ID
            invalid_ids = [cid for cid in gt_chunks if cid not in valid_chunk_ids]
            if invalid_ids:
                result.skipped_count += 1
                result.skipped.append(SkippedRecord(row=i, reason=f"chunk ID 不存在: {', '.join(invalid_ids[:3])}"))
                continue

            # 保留 quality_score / supporting_quotes 到 metadata
            extra = {}
            if "quality_score" in raw:
                extra["quality_score"] = raw["quality_score"]
            if "supporting_quotes" in raw:
                extra["supporting_quotes"] = raw["supporting_quotes"]
            merged_metadata = {**metadata, **extra} if extra else metadata

            record = GoldenRecord(
                project_id=project_id,
                query=query,
                ground_truth_chunks=gt_chunks,
                reference_answer=ref_answer,
                metadata=merged_metadata,
            )
            await self.golden_repo.save(record)
            result.success_count += 1

        return result
