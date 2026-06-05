-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 项目表
CREATE TABLE IF NOT EXISTS project (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 文档表
CREATE TABLE IF NOT EXISTS document (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    filename VARCHAR(512) NOT NULL,
    file_path VARCHAR(1024) NOT NULL,
    file_size BIGINT NOT NULL DEFAULT 0,
    file_type VARCHAR(32) NOT NULL,
    checksum VARCHAR(64) NOT NULL DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'uploaded',
    embedder_model VARCHAR(255) NOT NULL DEFAULT '',
    splitter_strategy VARCHAR(64) NOT NULL DEFAULT 'section_heading',
    chunk_size INT DEFAULT 500,
    chunk_overlap INT DEFAULT 50,
    splitter_min_chars INT DEFAULT 200,
    splitter_max_chars INT DEFAULT 2000,
    chunk_count INT DEFAULT 0,
    error_message TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 分块表
CREATE TABLE IF NOT EXISTS chunk (
    id VARCHAR(512) PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    index INT NOT NULL DEFAULT 0,
    heading VARCHAR(512) NOT NULL DEFAULT '',
    source_file VARCHAR(512) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 嵌入表
CREATE TABLE IF NOT EXISTS embedding (
    chunk_id VARCHAR(512) PRIMARY KEY REFERENCES chunk(id) ON DELETE CASCADE,
    vector VECTOR(512) NOT NULL,
    embedder_model VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 黄金测试集表
CREATE TABLE IF NOT EXISTS golden_dataset (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    ground_truth_chunks TEXT[] NOT NULL DEFAULT '{}',
    reference_answer TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_document_project_id ON document(project_id);
CREATE INDEX IF NOT EXISTS idx_document_status ON document(status);
CREATE INDEX IF NOT EXISTS idx_chunk_document_id ON chunk(document_id);
CREATE INDEX IF NOT EXISTS idx_embedding_chunk_id ON embedding(chunk_id);
CREATE INDEX IF NOT EXISTS idx_golden_dataset_project_id ON golden_dataset(project_id);

-- 向量索引 (IVFFlat，适合中等规模数据)
CREATE INDEX IF NOT EXISTS idx_embedding_vector ON embedding USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);