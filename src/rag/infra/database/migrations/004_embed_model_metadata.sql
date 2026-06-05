-- embed_model 表新增 metadata 列，存储 config.json 完整内容
ALTER TABLE embed_model ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
