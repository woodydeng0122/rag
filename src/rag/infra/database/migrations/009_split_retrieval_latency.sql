-- 009: 拆分检索耗时为嵌入耗时和向量检索耗时

ALTER TABLE golden_retrieval ADD COLUMN embed_latency_ms INT NOT NULL DEFAULT 0;
ALTER TABLE golden_retrieval ADD COLUMN search_latency_ms INT NOT NULL DEFAULT 0;
