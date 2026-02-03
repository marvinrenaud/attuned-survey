-- Rollback 034: Remove weekly activity limit columns and config
ALTER TABLE users DROP COLUMN IF EXISTS weekly_activity_count;
ALTER TABLE users DROP COLUMN IF EXISTS weekly_activity_reset_at;
DELETE FROM app_config WHERE key = 'free_tier_limit_mode';
