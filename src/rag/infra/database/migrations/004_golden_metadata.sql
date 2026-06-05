-- 黄金数据集表新增 metadata 字段
ALTER TABLE golden_dataset
    ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}';
