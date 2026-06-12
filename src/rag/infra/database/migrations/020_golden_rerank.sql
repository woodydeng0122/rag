-- 020: 新增黄金记录重排结果表

-- 重排结果主表（每条黄金记录最多一条，覆盖模式）
CREATE TABLE IF NOT EXISTS golden_rerank (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    golden_id UUID NOT NULL UNIQUE REFERENCES golden(id) ON DELETE CASCADE,
    top_k INT NOT NULL,
    latency_ms INT NOT NULL,
    model_name VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 重排结果明细表（每个重排后的 chunk 一条）
CREATE TABLE IF NOT EXISTS golden_rerank_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rerank_id UUID NOT NULL REFERENCES golden_rerank(id) ON DELETE CASCADE,
    chunk_id VARCHAR(512) NOT NULL,
    original_rank INT NOT NULL,
    rerank_score FLOAT NOT NULL,
    rerank_rank INT NOT NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_golden_rerank_golden_id ON golden_rerank(golden_id);
CREATE INDEX IF NOT EXISTS idx_golden_rerank_item_rerank_id ON golden_rerank_item(rerank_id);
