from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import health_router, retrieve_router, ask_router, evaluate_router
from .routes.project import router as project_router
from .routes.upload import router as upload_router
from .routes.document import router as document_router
from .middleware.logging import RequestLoggingMiddleware
from .middleware.response_wrapper import ResponseWrapperMiddleware
from .schemas.response import error, ERROR_CODE, TIMEOUT_CODE
from rag.infra.database.connection import init_pool, close_pool
from rag.bootstrap.settings import Settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：初始化数据库连接池
    settings = Settings.from_env()
    await init_pool(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )
    yield
    # 关闭：释放连接池
    await close_pool()


app = FastAPI(
    title="RAG API",
    description="基于 FastAPI 的 RAG 检索与问答服务",
    version="1.0.0",
    lifespan=lifespan,
)

# ========== 全局异常处理 — 统一返回 {code, message, result} 格式 ==========


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

# 响应包装中间件 — 自动包装 /api/ 路径的响应为统一格式
app.add_middleware(ResponseWrapperMiddleware)

# 请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# CORS 中间件 — 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3100", "http://localhost:3000"],
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
