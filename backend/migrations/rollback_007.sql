-- Rollback Migration 007: Remove Anonymous User Management
-- Reverses all changes from 007_add_anonymous_management.sql

-- Drop triggers
DROP TRIGGER IF EXISTS trigger_update_anonymous_profile_access ON profiles;

-- Drop trigger functions
DROP FUNCTION IF EXISTS update_anonymous_profile_access();

-- Drop views
DROP VIEW IF EXISTS anonymous_session_stats;
DROP VIEW IF EXISTS anonymous_sessions_to_cleanup;

-- Drop helper functions
DROP FUNCTION IF EXISTS link_anonymous_profile_to_session(TEXT, INTEGER);
DROP FUNCTION IF EXISTS touch_anonymous_session(TEXT);
DROP FUNCTION IF EXISTS cleanup_old_anonymous_sessions(INTEGER);

-- Drop indexes
DROP INDEX IF EXISTS idx_anonymous_sessions_created;
DROP INDEX IF EXISTS idx_anonymous_sessions_last_accessed;
DROP INDEX IF EXISTS idx_anonymous_sessions_profile;

-- Drop table
DROP TABLE IF EXISTS anonymous_sessions CASCADE;

-- Rollback complete

