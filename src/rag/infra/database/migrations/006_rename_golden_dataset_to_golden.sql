-- 006: 将 golden_dataset 重命名为 golden

ALTER TABLE golden_dataset RENAME TO golden;

-- 重命名索引
ALTER INDEX idx_golden_dataset_project_id RENAME TO idx_golden_project_id;
ALTER INDEX idx_golden_dataset_status RENAME TO idx_golden_status;
