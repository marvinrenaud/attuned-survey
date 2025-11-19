-- Rollback Migration 008: Remove RLS Policies
-- Reverses all changes from 008_add_rls_policies.sql

-- Drop helper functions
DROP FUNCTION IF EXISTS set_anonymous_session_context(TEXT);
DROP FUNCTION IF EXISTS is_premium_user(UUID);

-- Drop all RLS policies
DROP POLICY IF EXISTS ai_logs_select_own ON ai_generation_logs;
DROP POLICY IF EXISTS anonymous_sessions_access_own ON anonymous_sessions;
DROP POLICY IF EXISTS subscription_transactions_select_own ON subscription_transactions;
DROP POLICY IF EXISTS push_tokens_delete_own ON push_notification_tokens;
DROP POLICY IF EXISTS push_tokens_update_own ON push_notification_tokens;
DROP POLICY IF EXISTS push_tokens_insert_own ON push_notification_tokens;
DROP POLICY IF EXISTS push_tokens_select_own ON push_notification_tokens;
DROP POLICY IF EXISTS remembered_partners_delete_own ON remembered_partners;
DROP POLICY IF EXISTS remembered_partners_insert_own ON remembered_partners;
DROP POLICY IF EXISTS remembered_partners_select_own ON remembered_partners;
DROP POLICY IF EXISTS partner_connections_update_recipient ON partner_connections;
DROP POLICY IF EXISTS partner_connections_insert_own ON partner_connections;
DROP POLICY IF EXISTS partner_connections_select_own ON partner_connections;
DROP POLICY IF EXISTS activity_history_anonymous_access ON user_activity_history;
DROP POLICY IF EXISTS activity_history_insert_own ON user_activity_history;
DROP POLICY IF EXISTS activity_history_select_own ON user_activity_history;
DROP POLICY IF EXISTS activities_select_approved ON activities;
DROP POLICY IF EXISTS session_activities_insert_own ON session_activities;
DROP POLICY IF EXISTS session_activities_select_own ON session_activities;
DROP POLICY IF EXISTS sessions_anonymous_access ON sessions;
DROP POLICY IF EXISTS sessions_update_own ON sessions;
DROP POLICY IF EXISTS sessions_insert_own ON sessions;
DROP POLICY IF EXISTS sessions_select_participant ON sessions;
DROP POLICY IF EXISTS survey_progress_anonymous_access ON survey_progress;
DROP POLICY IF EXISTS survey_progress_update_own ON survey_progress;
DROP POLICY IF EXISTS survey_progress_insert_own ON survey_progress;
DROP POLICY IF EXISTS survey_progress_select_own ON survey_progress;
DROP POLICY IF EXISTS survey_submissions_insert_own ON survey_submissions;
DROP POLICY IF EXISTS survey_submissions_select_own ON survey_submissions;
DROP POLICY IF EXISTS profiles_anonymous_access ON profiles;
DROP POLICY IF EXISTS profiles_update_own ON profiles;
DROP POLICY IF EXISTS profiles_insert_own ON profiles;
DROP POLICY IF EXISTS profiles_select_partners ON profiles;
DROP POLICY IF EXISTS profiles_select_own ON profiles;
DROP POLICY IF EXISTS users_insert_own ON users;
DROP POLICY IF EXISTS users_update_own ON users;
DROP POLICY IF EXISTS users_select_own ON users;

-- Disable RLS on all tables
ALTER TABLE ai_generation_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE anonymous_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_transactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE push_notification_tokens DISABLE ROW LEVEL SECURITY;
ALTER TABLE remembered_partners DISABLE ROW LEVEL SECURITY;
ALTER TABLE partner_connections DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE activities DISABLE ROW LEVEL SECURITY;
ALTER TABLE session_activities DISABLE ROW LEVEL SECURITY;
ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE survey_progress DISABLE ROW LEVEL SECURITY;
ALTER TABLE survey_submissions DISABLE ROW LEVEL SECURITY;
ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- Rollback complete

