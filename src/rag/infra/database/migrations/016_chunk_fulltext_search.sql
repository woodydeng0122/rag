-- 为 chunk 表添加全文检索支持
-- 方案：Python 侧 jieba 分词 → search_tokens 列 → ts_vector 索引
-- 不依赖 PostgreSQL 中文分词插件

-- 1. 添加 search_tokens 列（存储 jieba 分词后的空格分隔文本）
ALTER TABLE chunk ADD COLUMN IF NOT EXISTS search_tokens TEXT NOT NULL DEFAULT '';

-- 2. 添加 search_vector 列（基于 search_tokens 构建，simple 分词器即可）
ALTER TABLE chunk ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;

-- 3. 创建 GIN 索引加速全文检索
CREATE INDEX IF NOT EXISTS idx_chunk_search_vector ON chunk USING GIN (search_vector);

-- 4. 创建触发器函数：INSERT/UPDATE 时自动从 search_tokens 构建 search_vector
CREATE OR REPLACE FUNCTION chunk_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('simple', coalesce(NEW.search_tokens, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5. 绑定触发器
DROP TRIGGER IF EXISTS trg_chunk_search_vector ON chunk;
CREATE TRIGGER trg_chunk_search_vector
    BEFORE INSERT OR UPDATE OF search_tokens ON chunk
    FOR EACH ROW
    EXECUTE FUNCTION chunk_search_vector_update();
