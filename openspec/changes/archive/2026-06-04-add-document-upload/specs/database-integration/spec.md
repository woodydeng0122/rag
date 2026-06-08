## ADDED Requirements

### Requirement: PostgreSQL with pgvector
系统 SHALL 使用 pgvector 扩展的 PostgreSQL 18 数据库，Docker 镜像为 `pgvector/pgvector:pg18`。

#### Scenario: Database starts with pgvector extension
- **WHEN** 执行 `docker compose up`
- **THEN** PostgreSQL 启动并自动启用 pgvector 扩展

### Requirement: Database connection pool
系统 SHALL 使用 asyncpg 连接池管理数据库连接。

#### Scenario: Connection pool initialized on startup
- **WHEN** FastAPI 应用启动
- **THEN** 系统创建 asyncpg 连接池，连接到 PostgreSQL（host=localhost, port=5434, database=rag-db）

#### Scenario: Connection pool closed on shutdown
- **WHEN** FastAPI 应用关闭
- **THEN** 系统关闭 asyncpg 连接池

### Requirement: Database schema
系统 SHALL 创建以下 5 张表：project、document、chunk、embedding、golden。

#### Scenario: Tables created on initialization
- **WHEN** 执行数据库初始化 SQL 脚本
- **THEN** 创建 project、document、chunk、embedding、golden 五张表，包含 proposal 中定义的所有字段

### Requirement: Document repository with asyncpg
系统 SHALL 提供 `PgDocumentRepository` 实现 `DocumentRepositoryPort` 接口，使用 asyncpg 操作 document 表。

#### Scenario: Save document record
- **WHEN** 调用 `document_repo.save(document)`
- **THEN** document 记录插入到 PostgreSQL document 表

#### Scenario: Get document by id
- **WHEN** 调用 `document_repo.get_by_id(doc_id)`
- **THEN** 返回对应的 document 实体

#### Scenario: List documents by project
- **WHEN** 调用 `document_repo.list_by_project(project_id)`
- **THEN** 返回该项目下所有 document 实体

#### Scenario: Update document status
- **WHEN** 调用 `document_repo.update_status(doc_id, status, error_message=None)`
- **THEN** 更新 document 的 status 和 updated_at 字段，如有 error_message 则一并更新

### Requirement: Chunk repository with asyncpg
系统 SHALL 提供 `PgChunkRepository` 实现 `ChunkRepositoryPort` 接口，使用 asyncpg 操作 chunk 表。

#### Scenario: Save chunks
- **WHEN** 调用 `chunk_repo.save(chunks)`
- **THEN** 所有 chunk 记录批量插入到 PostgreSQL chunk 表

### Requirement: Embedding repository with asyncpg
系统 SHALL 提供 `PgEmbeddingRepository` 实现 `EmbeddingRepositoryPort` 接口，使用 asyncpg + pgvector 操作 embedding 表。

#### Scenario: Save embeddings
- **WHEN** 调用 `embedding_repo.save(embeddings)`
- **THEN** 所有 embedding 记录批量插入到 PostgreSQL embedding 表，vector 字段使用 VECTOR 类型

### Requirement: Project repository with asyncpg
系统 SHALL 提供 `PgProjectRepository` 实现 `ProjectRepositoryPort` 接口，使用 asyncpg 操作 project 表。

#### Scenario: Save project
- **WHEN** 调用 `project_repo.save(project)`
- **THEN** project 记录插入到 PostgreSQL project 表

#### Scenario: List projects
- **WHEN** 调用 `project_repo.list()`
- **THEN** 返回所有 project 实体

#### Scenario: Get project by id
- **WHEN** 调用 `project_repo.get_by_id(project_id)`
- **THEN** 返回对应的 project 实体
