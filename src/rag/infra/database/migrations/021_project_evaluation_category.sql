-- 021: project_evaluation 加 category 列

ALTER TABLE project_evaluation ADD COLUMN IF NOT EXISTS category VARCHAR(20) NOT NULL DEFAULT 'recall';

CREATE INDEX IF NOT EXISTS idx_project_evaluation_category ON project_evaluation(category);
