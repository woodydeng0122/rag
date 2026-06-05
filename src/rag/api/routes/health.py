from fastapi import APIRouter

router = APIRouter(tags=["系统"])


@router.get("/health")
def health():
    """健康检查"""
    return {"status": "ok"}


@router.get("/")
def root():
    """API 概览"""
    return {
        "name": "RAG API",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "健康检查",
            "POST /retrieve": "检索相关分块",
            "POST /ask": "检索并生成回答",
            "POST /evaluate": "评测 Recall@K 和 MRR",
        },
    }
