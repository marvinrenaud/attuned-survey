-- Migration 034: Add weekly activity limit columns and feature flag
-- Date: 2026-02-03
-- Purpose: Support weekly/daily activity limit reset modes
-- Reversible: Yes, see rollback_034_add_weekly_activity_limit.sql

-- 1. Add weekly tracking columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_activity_count INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_activity_reset_at TIMESTAMPTZ DEFAULT NOW();

-- 2. Seed feature flag (default: weekly)
INSERT INTO app_config (key, value, description) VALUES
    ('free_tier_limit_mode', 'weekly', 'Activity limit mode: lifetime, weekly, or daily. Controls how free_tier_activity_limit resets.')
ON CONFLICT (key) DO NOTHING;

-- 3. Initialize weekly counters to 0 for all free users (fresh start)
UPDATE users
SET weekly_activity_count = 0,
    weekly_activity_reset_at = NOW()
WHERE subscription_tier = 'free';
