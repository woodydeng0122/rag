## Context

当前 RAG 系统的文档管理完全依赖手动操作：
- 文件直接放入 `docs/` 目录，无数据库记录
- 分块结果存储在 JSONL 文件中（`JsonlChunkRepository`）
- 嵌入向量存储在 JSONL 文件中（`JsonlEmbeddingRepository`）
- 没有前端界面管理文档生命周期
- 后端采用 Clean Architecture 分层：api → application → domain ← infra

数据库已有 Docker 配置（PostgreSQL 18，端口 5434），但为空库，无表结构。

## Goals / Non-Goals

**Goals:**
- 提供前端上传入口，支持单文件和 zip 上传
- 文件存储到 `docs/{upload_id}/` 目录，路径和元信息写入 PostgreSQL
- 支持 pgvector 向量存储，为后续向量检索打基础
- 手动触发分块+嵌入处理，状态可追踪
- 遵循现有 Clean Architecture 分层规则

**Non-Goals:**
- 不做用户认证/权限系统
- 不做自动触发处理（如上传后自动分块）
- 不做向量检索 API 的重构（本次只做存储，检索仍用现有 cosine_retriever）
- 不做 JSONL → PG 的数据迁移（新旧仓储并存）

## Decisions

### 1. 数据库驱动：原生 asyncpg

**选择**：asyncpg（不使用 ORM）

**理由**：
- 与 Clean Architecture 的 domain 层无依赖原则一致 — 不引入 ORM 实体类污染 domain
- asyncpg 性能最优，异步原生支持 FastAPI
- 仓储接口已在 domain/ports 定义，infra 层只需实现接口

**替代方案**：
- SQLAlchemy 2.0：成熟但引入较重依赖，ORM 实体与 domain entity 容易混淆
- SQLModel：与 Pydantic 集成好，但相对年轻，且同样有 ORM 实体问题

### 2. 向量存储：pgvector 扩展

**选择**：pgvector + VECTOR(384) 类型

**理由**：
- bge-small-zh-v1.5 输出维度为 384
- pgvector 提供原生余弦相似度检索，后续可替代内存中的 cosine_retriever
- 一个数据库同时存业务数据和向量，运维简单

**替代方案**：
- FLOAT[] 数组 + 应用层计算：不需要扩展但失去数据库层向量检索能力
- 独立向量数据库（Milvus/Qdrant）：过度设计，当前规模不需要

### 3. Docker 镜像：pgvector/pgvector:pg18

**选择**：替换 postgres:18-alpine 为 pgvector/pgvector:pg18

**理由**：基于 PostgreSQL 18 同时提供 pgvector 扩展，无需额外部署

### 4. zip 处理策略

**选择**：解压到 `docs/{upload_id}/` 保持目录结构，每个文件一条 document 记录

**理由**：
- 保持目录结构便于追溯文件来源
- 每文件独立记录便于单独管理处理状态
- upload_id 使用 UUID 避免冲突

### 5. 数据库迁移：SQL 脚本

**选择**：手动 SQL 脚本（`infra/database/migrations/`）

**理由**：
- 当前项目规模小，表结构简单
- 不引入 Alembic 等迁移框架的复杂度
- 后续需要时再引入

### 6. 文档处理触发：手动按钮

**选择**：前端手动点击"处理"按钮触发

**理由**：
- 分块+嵌入是计算密集型操作，用户应可控
- 便于用户在上传后调整分块参数再处理
- 避免上传大文件时阻塞请求

### 7. 仓储接口兼容：新增 PG 实现，保留 JSONL 实现

**选择**：新增 `PgChunkRepository` 和 `PgEmbeddingRepository`，不删除 JSONL 版本

**理由**：
- 现有 CLI 命令仍依赖 JSONL 仓储
- 渐进式迁移，降低风险
- 通过 Container 组合根切换实现

## Risks / Trade-offs

- **[Risk] asyncpg 无 ORM，SQL 维护成本** → SQL 集中在 infra/repositories/ 中，仓储接口隔离，SQL 变更只影响实现层
- **[Risk] pgvector 镜像体积比 alpine 大** → 开发环境可接受，生产环境可优化
- **[Risk] 大文件上传可能超时** → FastAPI 默认支持流式上传，后续可加断点续传
- **[Trade-off] 手动 SQL 迁移 vs Alembic** → 当前简单场景够用，表结构复杂后需引入迁移框架
- **[Trade-off] 新旧仓储并存** → 短期增加代码量，但降低迁移风险，长期统一后删除 JSONL 版本
