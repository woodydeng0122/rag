-- 补充 search_tokens 列 — jieba 分词结果存储
-- 016 迁移已执行但只有 search_vector 列，需要补充 search_tokens

-- 1. 添加 search_tokens 列
ALTER TABLE chunk ADD COLUMN IF NOT EXISTS search_tokens TEXT NOT NULL DEFAULT '';

-- 2. 修改触发器：从 search_tokens 而非 content 构建 search_vector
CREATE OR REPLACE FUNCTION chunk_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('simple', coalesce(NEW.search_tokens, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. 重新绑定触发器 — 监听 search_tokens 变化
DROP TRIGGER IF EXISTS trg_chunk_search_vector ON chunk;
CREATE TRIGGER trg_chunk_search_vector
    BEFORE INSERT OR UPDATE OF search_tokens ON chunk
    FOR EACH ROW
    EXECUTE FUNCTION chunk_search_vector_update();
