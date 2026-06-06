-- 为 golden_dataset 和 profile 表添加 updated_at 列

ALTER TABLE golden_dataset ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE profile ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
