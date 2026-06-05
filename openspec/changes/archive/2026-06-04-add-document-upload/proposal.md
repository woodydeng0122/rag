## Why

当前 RAG 系统的文档管理完全依赖手动操作：文件直接放入 `docs/` 目录，分块和嵌入结果存储在 JSONL 文件中，没有数据库记录文档的元信息、处理状态和配置参数。这导致无法通过前端管理文档生命周期，也无法追踪每个文档使用了什么分块策略和嵌入模型。需要一个前端入口让用户上传文件/zip，将文件路径和元信息持久化到 PostgreSQL，并支持后续手动触发分块+嵌入处理。

## What Changes

- 新增 PostgreSQL 数据库集成（使用 pgvector 扩展支持向量存储和检索），替代当前的 JSONL 文件存储
- 新增 `project` 表：管理项目（一个项目包含多文件多 zip）
- 新增 `document` 表：记录文件元信息、处理状态、分块策略参数、嵌入模型等
- 新增 `chunk` 表：关联文档与分块结果
- 新增 `embedding` 表：关联 chunk 与向量（使用 pgvector VECTOR 类型）
- 新增 `golden_dataset` 表：存储评测黄金测试集
- 新增后端上传 API：支持单文件和 zip 上传，zip 解压到 `docs/{upload_id}/` 保持目录结构
- 新增后端文档处理 API：手动触发分块+嵌入，状态流转 `uploaded → chunking → chunked → embedding → embedded → ready → error`
- 新增前端文档管理页面：上传文件/zip、查看文档列表和处理状态、手动触发处理
- 修改 docker-compose.yml：镜像从 `postgres:18-alpine` 换为 `pgvector/pgvector:pg18`
- 文件类型限制为 `.md`、`.txt`、`.pdf`

## Capabilities

### New Capabilities
- `document-upload`: 文件上传能力 — 支持单文件和 zip 上传，解压存储，写入数据库记录
- `document-process`: 文档处理能力 — 手动触发分块和嵌入，状态流转，结果写入 chunk/embedding 表
- `project-management`: 项目管理能力 — 创建项目，项目下包含多文档
- `database-integration`: 数据库集成能力 — PostgreSQL + pgvector 连接池、建表迁移、asyncpg 仓储实现
- `document-ui`: 前端文档管理界面 — 上传入口、文档列表、状态展示、处理按钮

### Modified Capabilities

## Impact

- **后端架构**：新增 database 基础设施层，新增 upload/document 路由和用例，domain 层新增 document/project 实体和仓库接口，infra 层新增 asyncpg 仓储实现
- **数据存储**：从 JSONL 文件迁移到 PostgreSQL + pgvector，chunk 和 embedding 仓储接口实现需新增 PG 版本
- **依赖**：新增 asyncpg、pgvector Docker 镜像
- **前端**：rag-web 新增文档管理页面和 API 对接
- **Docker**：docker-compose.yml 镜像变更
