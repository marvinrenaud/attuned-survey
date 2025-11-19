-- ============================================================================
-- COMBINED ROLLBACK: Reverse All MVP Migrations
-- ============================================================================
--
-- This file reverses all changes from migrations 003-008
-- Run this if you need to undo the MVP migration
--
-- WARNING: This will delete all data in new tables!
--
-- USAGE:
--   1. Open Supabase Dashboard → SQL Editor
--   2. Copy/paste this entire file
--   3. Click "Run"
--
-- ============================================================================

\echo '================================================'
\echo 'Starting MVP Rollback'
\echo 'This will REMOVE all MVP tables and columns'
\echo '================================================'

-- ============================================================================
-- ROLLBACK 008: Remove RLS Policies
-- ============================================================================

\echo 'Rollback 008: Removing RLS policies...'

DROP POLICY IF EXISTS remembered_partners_delete_own ON remembered_partners;
DROP POLICY IF EXISTS remembered_partners_insert_own ON remembered_partners;
DROP POLICY IF EXISTS remembered_partners_select_own ON remembered_partners;
DROP POLICY IF EXISTS partner_connections_insert_own ON partner_connections;
DROP POLICY IF EXISTS partner_connections_select_own ON partner_connections;
DROP POLICY IF EXISTS activity_history_insert_own ON user_activity_history;
DROP POLICY IF EXISTS activity_history_select_own ON user_activity_history;
DROP POLICY IF EXISTS sessions_insert_own ON sessions;
DROP POLICY IF EXISTS sessions_select_own ON sessions;
DROP POLICY IF EXISTS survey_progress_update_own ON survey_progress;
DROP POLICY IF EXISTS survey_progress_insert_own ON survey_progress;
DROP POLICY IF EXISTS survey_progress_select_own ON survey_progress;
DROP POLICY IF EXISTS profiles_update_own ON profiles;
DROP POLICY IF EXISTS profiles_insert_own ON profiles;
DROP POLICY IF EXISTS profiles_select_own ON profiles;
DROP POLICY IF EXISTS users_insert_own ON users;
DROP POLICY IF EXISTS users_update_own ON users;
DROP POLICY IF EXISTS users_select_own ON users;

ALTER TABLE remembered_partners DISABLE ROW LEVEL SECURITY;
ALTER TABLE partner_connections DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE survey_progress DISABLE ROW LEVEL SECURITY;
ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

\echo 'Rollback 008 complete ✓'

-- ============================================================================
-- ROLLBACK 007: Remove Anonymous Sessions
-- ============================================================================

\echo 'Rollback 007: Removing anonymous sessions...'

DROP FUNCTION IF EXISTS cleanup_old_anonymous_sessions(INTEGER);
DROP TABLE IF EXISTS anonymous_sessions CASCADE;

\echo 'Rollback 007 complete ✓'

-- ============================================================================
-- ROLLBACK 006: Remove Activity Tracking & Subscriptions
-- ============================================================================

\echo 'Rollback 006: Removing activity tracking...'

DROP TABLE IF EXISTS subscription_transactions CASCADE;
DROP TABLE IF EXISTS ai_generation_logs CASCADE;
DROP TABLE IF EXISTS user_activity_history CASCADE;

DROP TYPE IF EXISTS subscription_status_enum CASCADE;
DROP TYPE IF EXISTS feedback_type_enum CASCADE;
DROP TYPE IF EXISTS activity_type_enum CASCADE;

\echo 'Rollback 006 complete ✓'

-- ============================================================================
-- ROLLBACK 005: Remove Session Updates
-- ============================================================================

\echo 'Rollback 005: Removing session updates...'

ALTER TABLE sessions DROP COLUMN IF EXISTS connection_confirmed_at;
ALTER TABLE sessions DROP COLUMN IF EXISTS session_owner_user_id;
ALTER TABLE sessions DROP COLUMN IF EXISTS skip_count;
ALTER TABLE sessions DROP COLUMN IF EXISTS intimacy_level;
ALTER TABLE sessions DROP COLUMN IF EXISTS partner_anonymous_anatomy;
ALTER TABLE sessions DROP COLUMN IF EXISTS partner_anonymous_name;
ALTER TABLE sessions DROP COLUMN IF EXISTS partner_profile_id;
ALTER TABLE sessions DROP COLUMN IF EXISTS partner_user_id;
ALTER TABLE sessions DROP COLUMN IF EXISTS primary_profile_id;
ALTER TABLE sessions DROP COLUMN IF EXISTS primary_user_id;

DROP INDEX IF EXISTS idx_sessions_partner_user;
DROP INDEX IF EXISTS idx_sessions_primary_user;

DROP TYPE IF EXISTS intimacy_level_enum CASCADE;

\echo 'Rollback 005 complete ✓'

-- ============================================================================
-- ROLLBACK 004: Remove Partner System
-- ============================================================================

\echo 'Rollback 004: Removing partner system...'

DROP TABLE IF EXISTS push_notification_tokens CASCADE;
DROP TABLE IF EXISTS remembered_partners CASCADE;
DROP TABLE IF EXISTS partner_connections CASCADE;

DROP TYPE IF EXISTS platform_enum CASCADE;
DROP TYPE IF EXISTS connection_status_enum CASCADE;

\echo 'Rollback 004 complete ✓'

-- ============================================================================
-- ROLLBACK 003: Remove User Auth & Survey Progress
-- ============================================================================

\echo 'Rollback 003: Removing user auth...'

-- Remove indexes
DROP INDEX IF EXISTS idx_profiles_anonymous_session;
DROP INDEX IF EXISTS idx_profiles_user_id;

-- Remove columns from profiles
ALTER TABLE profiles DROP COLUMN IF EXISTS survey_version;
ALTER TABLE profiles DROP COLUMN IF EXISTS last_accessed_at;
ALTER TABLE profiles DROP COLUMN IF EXISTS anonymous_session_id;
ALTER TABLE profiles DROP COLUMN IF EXISTS is_anonymous;
ALTER TABLE profiles DROP COLUMN IF EXISTS user_id;

-- Remove columns from survey_submissions
ALTER TABLE survey_submissions DROP COLUMN IF EXISTS survey_progress_id;
ALTER TABLE survey_submissions DROP COLUMN IF EXISTS survey_version;

-- Drop survey_progress table
DROP INDEX IF EXISTS idx_survey_progress_anonymous;
DROP INDEX IF EXISTS idx_survey_progress_user_id;
DROP TABLE IF EXISTS survey_progress CASCADE;

-- Drop users table and trigger
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP FUNCTION IF EXISTS update_updated_at_column();

DROP INDEX IF EXISTS idx_users_subscription_tier;
DROP INDEX IF EXISTS idx_users_email;
DROP TABLE IF EXISTS users CASCADE;

-- Drop enums
DROP TYPE IF EXISTS survey_status_enum CASCADE;
DROP TYPE IF EXISTS profile_sharing_enum CASCADE;
DROP TYPE IF EXISTS subscription_tier_enum CASCADE;
DROP TYPE IF EXISTS auth_provider_enum CASCADE;

\echo 'Rollback 003 complete ✓'

-- ============================================================================
-- ROLLBACK COMPLETE
-- ============================================================================

\echo '================================================'
\echo 'MVP Rollback Complete! ✓'
\echo '================================================'
\echo ''
\echo 'All MVP changes have been reversed.'
\echo 'Your database is back to the prototype state.'
\echo ''
\echo 'To re-apply migrations: Run 000_APPLY_ALL_MIGRATIONS.sql'
\echo '================================================'

