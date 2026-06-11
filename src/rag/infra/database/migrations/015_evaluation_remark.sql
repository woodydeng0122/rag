-- 015: 评估记录新增备注字段

ALTER TABLE project_evaluation ADD COLUMN remark TEXT NOT NULL DEFAULT '';
