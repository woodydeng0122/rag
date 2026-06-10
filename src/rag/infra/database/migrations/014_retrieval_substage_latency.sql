-- 014: 新增检索子阶段耗时字段

ALTER TABLE golden_retrieval ADD COLUMN load_embeddings_latency_ms INT NOT NULL DEFAULT 0;
ALTER TABLE golden_retrieval ADD COLUMN load_project_latency_ms INT NOT NULL DEFAULT 0;
ALTER TABLE golden_retrieval ADD COLUMN load_embed_model_latency_ms INT NOT NULL DEFAULT 0;
ALTER TABLE golden_retrieval ADD COLUMN get_embedder_latency_ms INT NOT NULL DEFAULT 0;
ALTER TABLE golden_retrieval ADD COLUMN build_matrix_latency_ms INT NOT NULL DEFAULT 0;
