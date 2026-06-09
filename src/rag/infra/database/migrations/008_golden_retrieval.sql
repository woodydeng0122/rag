-- 008: 新增黄金记录检索结果表

-- 检索结果主表（每条黄金记录最多一条，覆盖模式）
CREATE TABLE IF NOT EXISTS golden_retrieval (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    golden_id UUID NOT NULL UNIQUE REFERENCES golden(id) ON DELETE CASCADE,
    max_k INT NOT NULL,
    latency_ms INT NOT NULL,
    embed_model_name VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 检索结果明细表（每个检索到的 chunk 一条）
CREATE TABLE IF NOT EXISTS golden_retrieval_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    retrieval_id UUID NOT NULL REFERENCES golden_retrieval(id) ON DELETE CASCADE,
    chunk_id VARCHAR(512) NOT NULL,
    score FLOAT NOT NULL,
    rank INT NOT NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_golden_retrieval_golden_id ON golden_retrieval(golden_id);
CREATE INDEX IF NOT EXISTS idx_golden_retrieval_item_retrieval_id ON golden_retrieval_item(retrieval_id);
