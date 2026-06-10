-- ============================================================
-- 修复 profile 表 id 列 — 从单例 integer 改为 UUID
-- ============================================================

-- 1. 移除相关约束和索引
ALTER TABLE profile DROP CONSTRAINT IF EXISTS profile_user_id_unique;
ALTER TABLE profile DROP CONSTRAINT IF EXISTS profile_id_check;
ALTER TABLE profile DROP CONSTRAINT IF EXISTS profile_id_not_null;
ALTER TABLE profile DROP CONSTRAINT IF EXISTS profile_pkey;

-- 2. 先添加新的 uuid_id 列并填充
ALTER TABLE profile ADD COLUMN uuid_id UUID DEFAULT gen_random_uuid() NOT NULL;

-- 3. 删除旧 id 列并重命名
ALTER TABLE profile DROP COLUMN id;
ALTER TABLE profile RENAME COLUMN uuid_id TO id;

-- 4. 设置默认值
ALTER TABLE profile ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- 5. 重建主键
ALTER TABLE profile ADD CONSTRAINT profile_pkey PRIMARY KEY (id);

-- 6. 重建 user_id 唯一索引
CREATE UNIQUE INDEX IF NOT EXISTS profile_user_id_unique ON profile(user_id);
