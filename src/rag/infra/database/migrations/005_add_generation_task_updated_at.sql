-- 为 generation_task 表添加 updated_at 列

ALTER TABLE generation_task ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
