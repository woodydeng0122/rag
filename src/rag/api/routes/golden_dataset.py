from fastapi import APIRouter, Depends, HTTPException

from rag.api.schemas.golden_dataset import (
    CreateGoldenDatasetRequest,
    UpdateGoldenDatasetRequest,
    GoldenDatasetResponse,
)
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/api/projects/{project_id}", tags=["golden-datasets"])


def _record_to_response(r) -> GoldenDatasetResponse:
    return GoldenDatasetResponse(
        id=r.id,
        project_id=r.project_id,
        query=r.query,
        ground_truth_chunks=r.ground_truth_chunks,
        reference_answer=r.reference_answer or "",
        retrieved_chunk_ids=r.retrieved_chunk_ids or [],
        is_hit=r.is_hit,
        hit_rank=r.hit_rank,
        evaluated_at=r.evaluated_at.isoformat() if r.evaluated_at else None,
        created_at=r.created_at.isoformat() if r.created_at else "",
    )


@router.get("/golden-datasets", response_model=list[GoldenDatasetResponse])
async def list_golden_datasets(
    project_id: str,
    container: Container = Depends(get_container),
):
    records = await container.golden_dataset_usecase.list_by_project(project_id)
    return [_record_to_response(r) for r in records]


@router.post("/golden-datasets", response_model=GoldenDatasetResponse)
async def create_golden_dataset(
    project_id: str,
    req: CreateGoldenDatasetRequest,
    container: Container = Depends(get_container),
):
    record = await container.golden_dataset_usecase.create(
        project_id=project_id,
        query=req.query,
        ground_truth_chunks=req.ground_truth_chunks,
        reference_answer=req.reference_answer,
    )
    return _record_to_response(record)


@router.put("/golden-datasets/{record_id}", response_model=GoldenDatasetResponse)
async def update_golden_dataset(
    project_id: str,
    record_id: str,
    req: UpdateGoldenDatasetRequest,
    container: Container = Depends(get_container),
):
    try:
        record = await container.golden_dataset_usecase.update(
            record_id=record_id,
            query=req.query,
            ground_truth_chunks=req.ground_truth_chunks,
            reference_answer=req.reference_answer,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _record_to_response(record)


@router.delete("/golden-datasets/{record_id}")
async def delete_golden_dataset(
    project_id: str,
    record_id: str,
    container: Container = Depends(get_container),
):
    deleted = await container.golden_dataset_usecase.delete(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="黄金记录不存在")
    return {"detail": "删除成功"}
