-- ============================================================
-- 002: golden_dataset 加 status 列 + 新建 generation_task 表
-- ============================================================

-- ① golden_dataset 增加 status 列
ALTER TABLE golden_dataset ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'approved';
CREATE INDEX IF NOT EXISTS idx_golden_dataset_status ON golden_dataset(status);

-- ② 新建 generation_task 表
CREATE TABLE IF NOT EXISTS generation_task (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL DEFAULT 'running',
    total INT NOT NULL DEFAULT 0,
    completed INT NOT NULL DEFAULT 0,
    failed INT NOT NULL DEFAULT 0,
    document_ids TEXT[] NOT NULL DEFAULT '{}',
    chunk_ids TEXT[] NOT NULL DEFAULT '{}',
    config JSONB NOT NULL DEFAULT '{}',
    error_message TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ DEFAULT NULL
);
CREATE INDEX IF NOT EXISTS idx_generation_task_project_id ON generation_task(project_id);
