## MODIFIED Requirements

### Requirement: Processing parameters from document record
系统 SHALL 从 document 表读取分块策略和参数来执行处理，嵌入模型从项目记录获取。

#### Scenario: Process with fixed_size strategy
- **WHEN** document 的 splitter_strategy 为 `fixed`，chunk_size 为 500，chunk_overlap 为 50
- **THEN** 系统使用 FixedSizeSplitter 并传入对应参数执行分块

#### Scenario: Process with section_heading strategy
- **WHEN** document 的 splitter_strategy 为 `section_heading`，splitter_min_chars 为 200，splitter_max_chars 为 2000
- **THEN** 系统使用 SectionHeadingSplitter 并传入对应参数执行分块

#### Scenario: Process with project embed model
- **WHEN** 文档所属项目的 embed_model_id 指向 `BAAI/bge-small-zh-v1.5`（dimension=512）
- **THEN** 系统加载该模型的 SentenceTransformer 实例执行嵌入，写入 embedding 表的向量维度为 512

### Requirement: Chunk and embedding records created
系统 SHALL 在处理过程中将分块结果写入 chunk 表，嵌入结果写入 embedding 表。

#### Scenario: Chunks created after chunking phase
- **WHEN** 文档分块完成
- **THEN** chunk 表中为每个分块创建记录，包含 id、document_id、content、index、heading、source_file

#### Scenario: Embeddings created after embedding phase
- **WHEN** 文档嵌入完成
- **THEN** embedding 表中为每个 chunk 创建记录，包含 chunk_id、vector（维度与项目 embed_dimension 一致）、embedder_model（从项目关联的 embed_model.name 获取）

## REMOVED Requirements

### Requirement: Embedder model recorded
**Reason**: 嵌入模型信息不再存储在 document 表，改为从项目关联的 embed_model 表获取
**Migration**: document 表删除 embedder_model 字段，模型信息通过 project → embed_model 关联查询
