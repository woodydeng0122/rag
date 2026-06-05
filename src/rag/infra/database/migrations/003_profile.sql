-- 用户配置表（单例，仅一行）
CREATE TABLE IF NOT EXISTS profile (
    id INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    active_project_id UUID REFERENCES project(id) ON DELETE SET NULL
);

-- 插入默认行
INSERT INTO profile (id, active_project_id) VALUES (1, NULL) ON CONFLICT (id) DO NOTHING;
