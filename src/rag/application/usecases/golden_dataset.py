from rag.domain.entities.golden_record import GoldenRecord
from rag.domain.ports.golden_dataset_repository import GoldenDatasetRepositoryPort


class GoldenDatasetUseCase:
    """黄金数据集 CRUD 用例"""

    def __init__(self, golden_repo: GoldenDatasetRepositoryPort):
        self.golden_repo = golden_repo

    async def create(self, project_id: str, query: str, ground_truth_chunks: list[str], reference_answer: str = "") -> GoldenRecord:
        record = GoldenRecord(
            project_id=project_id,
            query=query,
            ground_truth_chunks=ground_truth_chunks,
            reference_answer=reference_answer,
        )
        return await self.golden_repo.save(record)

    async def get(self, record_id: str) -> GoldenRecord | None:
        return await self.golden_repo.get_by_id(record_id)

    async def list_by_project(self, project_id: str) -> list[GoldenRecord]:
        return await self.golden_repo.list_by_project(project_id)

    async def update(self, record_id: str, query: str, ground_truth_chunks: list[str], reference_answer: str = "") -> GoldenRecord:
        record = await self.golden_repo.get_by_id(record_id)
        if record is None:
            raise ValueError(f"黄金记录 {record_id} 不存在")
        record.query = query
        record.ground_truth_chunks = ground_truth_chunks
        record.reference_answer = reference_answer
        return await self.golden_repo.update(record)

    async def delete(self, record_id: str) -> bool:
        return await self.golden_repo.delete(record_id)
