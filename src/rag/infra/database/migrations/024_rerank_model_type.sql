-- 022: embed_model 加 model_type 列，project 加 rerank_model_id 列

-- embed_model 表新增 model_type 列
ALTER TABLE embed_model ADD COLUMN IF NOT EXISTS model_type VARCHAR(32) NOT NULL DEFAULT 'embed';

-- 已有行补全 model_type
UPDATE embed_model SET model_type = 'embed' WHERE model_type IS NULL;

-- project 表新增 rerank_model_id 列
ALTER TABLE project ADD COLUMN IF NOT EXISTS rerank_model_id UUID REFERENCES embed_model(id) DEFAULT NULL;

-- 索引
CREATE INDEX IF NOT EXISTS idx_project_rerank_model_id ON project(rerank_model_id);
