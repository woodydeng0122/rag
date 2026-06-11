-- golden_retrieval 和 project_evaluation 表添加 strategy 列
ALTER TABLE golden_retrieval ADD COLUMN IF NOT EXISTS strategy VARCHAR(20) NOT NULL DEFAULT 'hybrid';
ALTER TABLE project_evaluation ADD COLUMN IF NOT EXISTS strategy VARCHAR(20) NOT NULL DEFAULT 'hybrid';
