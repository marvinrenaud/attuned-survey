-- Rollback Migration 006: Remove Activity Tracking & Subscriptions
-- Reverses all changes from 006_add_activity_tracking.sql

-- Drop helper functions
DROP FUNCTION IF EXISTS check_daily_activity_limit(UUID, INTEGER);
DROP FUNCTION IF EXISTS reset_daily_activity_counts();
DROP FUNCTION IF EXISTS check_theme_diversity(TEXT, JSONB);
DROP FUNCTION IF EXISTS get_excluded_activities_for_user(UUID, TEXT);

-- Drop trigger for subscription_transactions
DROP TRIGGER IF EXISTS update_subscription_transactions_updated_at ON subscription_transactions;

-- Drop indexes and tables for subscription_transactions
DROP INDEX IF EXISTS idx_subscription_created;
DROP INDEX IF EXISTS idx_subscription_expires;
DROP INDEX IF EXISTS idx_subscription_status;
DROP INDEX IF EXISTS idx_subscription_platform_tx;
DROP INDEX IF EXISTS idx_subscription_user;
DROP TABLE IF EXISTS subscription_transactions CASCADE;

-- Drop indexes and tables for ai_generation_logs
DROP INDEX IF EXISTS idx_ai_logs_generation_time;
DROP INDEX IF EXISTS idx_ai_logs_model;
DROP INDEX IF EXISTS idx_ai_logs_approved;
DROP INDEX IF EXISTS idx_ai_logs_created;
DROP INDEX IF EXISTS idx_ai_logs_session;
DROP TABLE IF EXISTS ai_generation_logs CASCADE;

-- Drop indexes and tables for user_activity_history
DROP INDEX IF EXISTS idx_activity_history_feedback;
DROP INDEX IF EXISTS idx_activity_history_skipped;
DROP INDEX IF EXISTS idx_activity_history_activity;
DROP INDEX IF EXISTS idx_activity_history_session;
DROP INDEX IF EXISTS idx_activity_history_anon_presented;
DROP INDEX IF EXISTS idx_activity_history_user_presented;
DROP TABLE IF EXISTS user_activity_history CASCADE;

-- Drop enums
DROP TYPE IF EXISTS subscription_status_enum CASCADE;
DROP TYPE IF EXISTS feedback_type_enum CASCADE;
DROP TYPE IF EXISTS activity_type_enum CASCADE;

-- Rollback complete

