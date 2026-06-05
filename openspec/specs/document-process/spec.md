# Document Process

## Purpose

提供文档分块和嵌入的处理能力，包括手动触发处理、状态流转和参数配置。

## Requirements

### Requirement: Manual trigger document processing
系统 SHALL 提供手动触发文档分块+嵌入的 API 端点。

#### Scenario: Trigger processing for an uploaded document
- **WHEN** 用户通过 `POST /api/documents/{document_id}/process` 触发处理
- **THEN** 系统将 document status 从 `uploaded` 变更为 `chunking`，执行分块，再变更为 `chunked`，执行嵌入，最终变更为 `ready`

### Requirement: Status tracking
系统 SHALL 支持文档处理状态的完整流转：`uploaded → chunking → chunked → embedding → embedded → ready`，以及异常状态 `error`。

#### Scenario: Processing succeeds
- **WHEN** 文档处理成功完成
- **THEN** document status 为 `ready`，chunk_count 字段填入实际分块数量

#### Scenario: Processing fails
- **WHEN** 分块或嵌入过程中发生错误
- **THEN** document status 变更为 `error`，error_message 字段记录错误信息

#### Scenario: Query document status
- **WHEN** 用户查询文档列表
- **THEN** 每个文档显示当前 status 值

### Requirement: Processing parameters from document record
系统 SHALL 从 document 表读取分块策略和参数来执行处理。

#### Scenario: Process with fixed_size strategy
- **WHEN** document 的 splitter_strategy 为 `fixed`，chunk_size 为 500，chunk_overlap 为 50
- **THEN** 系统使用 FixedSizeSplitter 并传入对应参数执行分块

#### Scenario: Process with section_heading strategy
- **WHEN** document 的 splitter_strategy 为 `section_heading`，splitter_min_chars 为 200，splitter_max_chars 为 2000
- **THEN** 系统使用 SectionHeadingSplitter 并传入对应参数执行分块

### Requirement: Chunk and embedding records created
系统 SHALL 在处理过程中将分块结果写入 chunk 表，嵌入结果写入 embedding 表。

#### Scenario: Chunks created after chunking phase
- **WHEN** 文档分块完成
- **THEN** chunk 表中为每个分块创建记录，包含 id、document_id、content、index、heading、source_file

#### Scenario: Embeddings created after embedding phase
- **WHEN** 文档嵌入完成
- **THEN** embedding 表中为每个 chunk 创建记录，包含 chunk_id、vector（VECTOR(384)类型）、embedder_model

### Requirement: Embedder model recorded
系统 SHALL 将使用的嵌入模型名称记录到 document 表的 embedder_model 字段和 embedding 表的 embedder_model 字段。

#### Scenario: Model name stored
- **WHEN** 使用 `models/BAAI/bge-small-zh-v1.5` 完成嵌入
- **THEN** document.embedder_model 和 embedding.embedder_model 均为 `models/BAAI/bge-small-zh-v1.5`
