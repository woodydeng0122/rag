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

-- 4. embedding 表向量列保持 VECTOR(512) 不变
-- pgvector 的 IVFFlat/HNSW 索引要求列有固定维度，不支持无维度 VECTOR 列建索引
-- 维度校验由应用层负责：创建项目时 embed_dimension 必须与 embedding 表维度一致

-- 索引
CREATE INDEX IF NOT EXISTS idx_project_embed_model_id ON project(embed_model_id);
