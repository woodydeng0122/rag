-- 1. 新增嵌入模型注册表
CREATE TABLE IF NOT EXISTS embed_model (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    dimension INT NOT NULL,
    description TEXT DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'offline',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. project 表新增 embed_model_id 和 embed_dimension
ALTER TABLE project ADD COLUMN IF NOT EXISTS embed_model_id UUID REFERENCES embed_model(id);
ALTER TABLE project ADD COLUMN IF NOT EXISTS embed_dimension INT NOT NULL DEFAULT 512;

-- 3. document 表删除 embedder_model 字段
ALTER TABLE document DROP COLUMN IF EXISTS embedder_model;

-- 4. embedding 表向量列从 VECTOR(512) 改为 VECTOR（不指定维度）
-- pgvector 不支持 ALTER COLUMN 修改维度，需要重建列
ALTER TABLE embedding DROP COLUMN IF EXISTS vector;
ALTER TABLE embedding ADD COLUMN vector VECTOR NOT NULL;

-- 重建向量索引
DROP INDEX IF EXISTS idx_embedding_vector;
CREATE INDEX IF NOT EXISTS idx_embedding_vector ON embedding USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);

-- 索引
CREATE INDEX IF NOT EXISTS idx_project_embed_model_id ON project(embed_model_id);
