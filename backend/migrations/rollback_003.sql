-- Rollback Migration 003: Remove User Authentication & Survey Auto-Save
-- Reverses all changes from 003_add_user_auth.sql

-- Drop indexes from profiles
DROP INDEX IF EXISTS idx_profiles_unique_user;
DROP INDEX IF EXISTS idx_profiles_last_accessed;
DROP INDEX IF EXISTS idx_profiles_is_anonymous;
DROP INDEX IF EXISTS idx_profiles_anonymous_session;
DROP INDEX IF EXISTS idx_profiles_user_id;

-- Remove columns from profiles
ALTER TABLE profiles DROP COLUMN IF EXISTS survey_version;
ALTER TABLE profiles DROP COLUMN IF EXISTS last_accessed_at;
ALTER TABLE profiles DROP COLUMN IF EXISTS anonymous_session_id;
ALTER TABLE profiles DROP COLUMN IF EXISTS is_anonymous;
ALTER TABLE profiles DROP COLUMN IF EXISTS user_id;

-- Drop index from survey_submissions
DROP INDEX IF EXISTS idx_survey_submissions_version;

-- Remove columns from survey_submissions
ALTER TABLE survey_submissions DROP COLUMN IF EXISTS survey_progress_id;
ALTER TABLE survey_submissions DROP COLUMN IF EXISTS survey_version;

-- Drop survey_progress table and related objects
DROP INDEX IF EXISTS idx_survey_progress_unique_anon_version;
DROP INDEX IF EXISTS idx_survey_progress_unique_user_version;
DROP INDEX IF EXISTS idx_survey_progress_version;
DROP INDEX IF EXISTS idx_survey_progress_status;
DROP INDEX IF EXISTS idx_survey_progress_anonymous;
DROP INDEX IF EXISTS idx_survey_progress_user_id;

DROP TABLE IF EXISTS survey_progress CASCADE;

-- Drop users table and related objects
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP FUNCTION IF EXISTS update_updated_at_column();

DROP INDEX IF EXISTS idx_users_created_at;
DROP INDEX IF EXISTS idx_users_subscription_tier;
DROP INDEX IF EXISTS idx_users_email;

DROP TABLE IF EXISTS users CASCADE;

-- Drop enums
DROP TYPE IF EXISTS survey_status_enum CASCADE;
DROP TYPE IF EXISTS profile_sharing_enum CASCADE;
DROP TYPE IF EXISTS subscription_tier_enum CASCADE;
DROP TYPE IF EXISTS auth_provider_enum CASCADE;

-- Rollback complete

