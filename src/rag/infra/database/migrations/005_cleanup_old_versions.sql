-- 清理重编号前的旧版本记录
-- 002_profile → 003_profile, 003_golden_eval_fields → 004_golden_eval_fields
DELETE FROM schema_migrations WHERE version IN ('002_profile', '003_golden_eval_fields');
