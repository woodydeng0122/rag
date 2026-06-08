from fastapi import APIRouter, Depends, UploadFile, File, Form

from rag.api.presenters.document import DocumentPresenter
from rag.bootstrap.container import Container, get_container
from rag.domain.value_objects.splitter_config import SplitterConfig

router = APIRouter(prefix="/api/projects/{project_id}", tags=["upload"])


@router.post("/documents")
async def upload_documents(
    project_id: str,
    file: UploadFile = File(...),
    splitter_strategy: str = Form("section_heading"),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(50),
    splitter_min_chars: int = Form(200),
    splitter_max_chars: int = Form(2000),
    container: Container = Depends(get_container),
):
    file_content = await file.read()
    filename = file.filename or "unknown"

    splitter_config = SplitterConfig(
        strategy=splitter_strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        min_chars=splitter_min_chars,
        max_chars=splitter_max_chars,
    )

    try:
        documents = await container.upload_usecase.execute(
            project_id=project_id,
            filename=filename,
            file_content=file_content,
            splitter_config=splitter_config,
        )
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))

    return DocumentPresenter.to_upload_response(documents)
