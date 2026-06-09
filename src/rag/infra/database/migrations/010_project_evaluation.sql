-- 010: 新增项目评估统计表

CREATE TABLE IF NOT EXISTS project_evaluation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    top_k INT NOT NULL,
    golden_total INT NOT NULL,
    golden_retrieved INT NOT NULL,
    recall_at_k FLOAT NOT NULL,
    mrr FLOAT NOT NULL,
    hit_rate FLOAT NOT NULL,
    full_hit_count INT NOT NULL,
    zero_hit_count INT NOT NULL,
    avg_latency_ms FLOAT NOT NULL,
    avg_embed_latency_ms FLOAT NOT NULL,
    avg_search_latency_ms FLOAT NOT NULL,
    embed_model_name VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_project_evaluation_project_id ON project_evaluation(project_id);
