-- 将 document 表的 file_path 列重命名为 storage_key
ALTER TABLE document RENAME COLUMN file_path TO storage_key;
