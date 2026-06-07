from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routes import health_router, retrieve_router, ask_router, evaluate_router
from .routes.project import router as project_router
from .routes.upload import router as upload_router
from .routes.document import router as document_router
from .routes.embed_model import router as embed_model_router
from .routes.golden_dataset import router as golden_dataset_router
from .routes.profile import router as profile_router
from .middleware.response_wrapper import ResponseWrapperMiddleware
from .schemas.response import error, ERROR_CODE, TIMEOUT_CODE
from rag.bootstrap.startup import startup, shutdown
from rag.bootstrap.container import get_container


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = get_container()
    await startup(container)
    yield
    await shutdown()


app = FastAPI(
    title="RAG API",
    description="基于 FastAPI 的 RAG 检索与问答服务",
    version="1.0.0",
    lifespan=lifespan,
)

# ========== 全局异常处理 — 统一返回 {code, message, result} 格式 ==========


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP 异常（404/400 等）→ 统一格式"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error(message=str(exc.detail), code=ERROR_CODE),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """业务校验错误 → 400"""
    return JSONResponse(
        status_code=400,
        content=error(message=str(exc), code=ERROR_CODE),
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    """未捕获异常 → 500"""
    return JSONResponse(
        status_code=500,
        content=error(message="服务器内部错误", code=ERROR_CODE),
    )


# ========== 中间件 ==========

# 响应包装 + 请求日志中间件
app.add_middleware(ResponseWrapperMiddleware)

# CORS 中间件 — 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3100"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 注册路由 ==========

app.include_router(health_router)
app.include_router(retrieve_router)
app.include_router(ask_router)
app.include_router(evaluate_router)
app.include_router(project_router)
app.include_router(upload_router)
app.include_router(document_router)
app.include_router(embed_model_router)
app.include_router(golden_dataset_router)
app.include_router(profile_router)

from argparse import ArgumentParser
def register_args(p: ArgumentParser):
    pass

def handle(args, container):
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)