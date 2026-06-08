-- 007: 删除评测相关列

-- golden 表
ALTER TABLE golden DROP COLUMN IF EXISTS retrieved_chunk_ids;
ALTER TABLE golden DROP COLUMN IF EXISTS is_hit;
ALTER TABLE golden DROP COLUMN IF EXISTS hit_rank;
ALTER TABLE golden DROP COLUMN IF EXISTS evaluated_at;

-- project 表
ALTER TABLE project DROP COLUMN IF EXISTS eval_recall_at_10;
ALTER TABLE project DROP COLUMN IF EXISTS eval_mrr;
ALTER TABLE project DROP COLUMN IF EXISTS eval_answerable;
ALTER TABLE project DROP COLUMN IF EXISTS eval_total;
ALTER TABLE project DROP COLUMN IF EXISTS eval_latency_avg_ms;
ALTER TABLE project DROP COLUMN IF EXISTS evaluated_at;
