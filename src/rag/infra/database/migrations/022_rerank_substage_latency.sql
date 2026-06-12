-- 022: 重排结果新增子阶段延迟字段

ALTER TABLE golden_rerank ADD COLUMN load_retrieval_latency_ms INT NOT NULL DEFAULT 0;
ALTER TABLE golden_rerank ADD COLUMN load_chunks_latency_ms INT NOT NULL DEFAULT 0;
ALTER TABLE golden_rerank ADD COLUMN predict_latency_ms INT NOT NULL DEFAULT 0;
