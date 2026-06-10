-- ============================================================
-- 用户体系迁移 — 新增 user 表、改造 profile 为 per-user、project 加 user_id
-- ============================================================

-- 用户表
CREATE TABLE IF NOT EXISTS "user" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- profile 表改造：新增 user_id，从单例变为 per-user
ALTER TABLE profile ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES "user"(id) ON DELETE CASCADE;
ALTER TABLE profile ADD CONSTRAINT profile_user_id_unique UNIQUE (user_id);

-- 注意：迁移后需通过 CLI 创建首个用户，然后手动将现有 profile 和 project 关联到该用户
-- 以下为辅助迁移步骤（在首个用户创建后执行）：
-- UPDATE profile SET user_id = '<first_user_id>' WHERE id = 1;
-- UPDATE project SET user_id = '<first_user_id>' WHERE user_id IS NULL;

-- project 表新增 user_id
ALTER TABLE project ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES "user"(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_project_user_id ON project(user_id);

-- 索引
CREATE INDEX IF NOT EXISTS idx_profile_user_id ON profile(user_id);
