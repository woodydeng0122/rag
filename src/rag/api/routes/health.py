from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["系统"])


@router.get("/health")
def health():
    """健康检查"""
    return {"status": "ok"}
