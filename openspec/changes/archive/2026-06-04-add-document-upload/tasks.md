## 1. 数据库基础设施

- [x] 1.1 修改 docker-compose.yml：镜像从 `postgres:18-alpine` 换为 `pgvector/pgvector:pg18`，添加初始化 SQL 挂载
- [x] 1.2 创建数据库初始化 SQL 脚本 `src/rag/infra/database/migrations/001_init.sql`：启用 pgvector 扩展，创建 project、document、chunk、embedding、golden 五张表
- [x] 1.3 创建数据库连接模块 `src/rag/infra/database/connection.py`：asyncpg 连接池管理（init_pool、get_pool、close_pool）
- [x] 1.4 启动数据库并验证建表成功

## 2. Domain 层扩展

- [x] 2.1 创建 `src/rag/domain/entities/project.py`：Project 实体（id, name, description, created_at, updated_at）
- [x] 2.2 创建 `src/rag/domain/entities/document.py`：Document 实体（id, project_id, filename, file_path, file_size, file_type, checksum, status, embedder_model, splitter_strategy, chunk_size, chunk_overlap, splitter_min_chars, splitter_max_chars, chunk_count, error_message, created_at, updated_at）
- [x] 2.3 创建 `src/rag/domain/ports/project_repository.py`：ProjectRepositoryPort 接口（save, get_by_id, list）
- [x] 2.4 创建 `src/rag/domain/ports/document_repository.py`：DocumentRepositoryPort 接口（save, get_by_id, list_by_project, update_status, update_chunk_count）
- [x] 2.5 扩展 `src/rag/domain/ports/chunk_repository.py`：添加 save_batch 和 list_by_document 方法签名
- [x] 2.6 扩展 `src/rag/domain/ports/embedding_repository.py`：添加 save_batch 方法签名

## 3. Infra 层 — 仓储实现

- [x] 3.1 创建 `src/rag/infra/repositories/pg_project_repository.py`：PgProjectRepository 实现
- [x] 3.2 创建 `src/rag/infra/repositories/pg_document_repository.py`：PgDocumentRepository 实现
- [x] 3.3 创建 `src/rag/infra/repositories/pg_chunk_repository.py`：PgChunkRepository 实现
- [x] 3.4 创建 `src/rag/infra/repositories/pg_embedding_repository.py`：PgEmbeddingRepository 实现（含 pgvector VECTOR 类型写入）

## 4. Application 层 — 用例

- [x] 4.1 创建 `src/rag/application/usecases/upload.py`：UploadUseCase — 接收文件/zip，存储到 docs/{upload_id}/，创建 document 记录
- [x] 4.2 创建 `src/rag/application/usecases/process_document.py`：ProcessDocumentUseCase — 手动触发分块+嵌入，状态流转，结果写入 chunk/embedding 表
- [x] 4.3 创建 `src/rag/application/results/upload_result.py`：UploadResult 输出模型

## 5. API 层 — 路由和 Schema

- [x] 5.1 创建 `src/rag/api/schemas/project.py`：项目相关请求/响应 Pydantic 模型
- [x] 5.2 创建 `src/rag/api/schemas/upload.py`：上传相关请求/响应 Pydantic 模型
- [x] 5.3 创建 `src/rag/api/schemas/document.py`：文档相关请求/响应 Pydantic 模型
- [x] 5.4 创建 `src/rag/api/routes/project.py`：项目 CRUD 路由（POST /api/projects, GET /api/projects, GET /api/projects/{id}）
- [x] 5.5 创建 `src/rag/api/routes/upload.py`：上传路由（POST /api/projects/{project_id}/documents）
- [x] 5.6 创建 `src/rag/api/routes/document.py`：文档管理路由（POST /api/documents/{id}/process, GET /api/projects/{project_id}/documents）
- [x] 5.7 修改 `src/rag/api/app.py`：注册新路由，添加 lifespan 事件管理数据库连接池
- [x] 5.8 修改 `src/rag/bootstrap/container.py`：注入 PG 仓储实现，新增 upload 和 process_document 用例
- [x] 5.9 修改 `src/rag/bootstrap/settings.py`：添加数据库连接配置（DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD）

## 6. 前端 — rag-web

- [x] 6.1 创建 `rag-web/src/api/sys/model/documentModel.ts`：项目、文档、上传相关 TypeScript 类型定义
- [x] 6.2 创建 `rag-web/src/api/sys/document.ts`：项目 CRUD、文档上传、文档处理 API 调用
- [x] 6.3 创建 `rag-web/src/views/document/index.vue`：文档管理主页面（项目选择、上传组件、文档列表、处理按钮）
- [x] 6.4 添加路由配置：在 `rag-web/src/router/routes/modules/` 下添加文档管理路由
- [x] 6.5 添加菜单配置：在左侧菜单中添加文档管理入口

## 7. 集成验证

- [x] 7.1 启动 Docker 数据库，验证 pgvector 扩展和表结构
- [x] 7.2 启动 FastAPI 后端，验证项目 CRUD、文件上传、文档处理 API
- [x] 7.3 启动前端，验证上传文件、查看文档列表、触发处理完整流程
