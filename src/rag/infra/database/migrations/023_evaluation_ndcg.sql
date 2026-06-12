-- 023: 项目评估新增 NDCG 指标

ALTER TABLE project_evaluation ADD COLUMN ndcg FLOAT NOT NULL DEFAULT 0;
