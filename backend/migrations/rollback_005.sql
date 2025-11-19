-- Rollback Migration 005: Remove Session Updates
-- Reverses all changes from 005_update_sessions.sql

-- Drop helper functions
DROP FUNCTION IF EXISTS reset_skip_count_on_activity();
DROP FUNCTION IF EXISTS get_partner_profile_visibility(UUID, UUID);

-- Drop indexes
DROP INDEX IF EXISTS idx_sessions_status;
DROP INDEX IF EXISTS idx_sessions_intimacy_level;
DROP INDEX IF EXISTS idx_sessions_owner;
DROP INDEX IF EXISTS idx_sessions_partner_profile;
DROP INDEX IF EXISTS idx_sessions_partner_user;
DROP INDEX IF EXISTS idx_sessions_primary_profile;
DROP INDEX IF EXISTS idx_sessions_primary_user;

-- Remove columns from sessions table
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

-- Drop enum
DROP TYPE IF EXISTS intimacy_level_enum CASCADE;

-- Rollback complete

