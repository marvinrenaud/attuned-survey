-- Rollback Migration 035: Enrich JIT activity tracking

-- Remove indexes first
DROP INDEX IF EXISTS idx_session_activities_skipped;
DROP INDEX IF EXISTS idx_session_activities_consumed;

-- Remove added columns
ALTER TABLE session_activities DROP COLUMN IF EXISTS was_skipped;
ALTER TABLE session_activities DROP COLUMN IF EXISTS consumed_at;
ALTER TABLE session_activities DROP COLUMN IF EXISTS secondary_player_ids;
ALTER TABLE session_activities DROP COLUMN IF EXISTS primary_player_id;
ALTER TABLE session_activities DROP COLUMN IF EXISTS intensity_phase;

-- Restore NOT NULL constraints
-- NOTE: This may fail if NULL values exist in the data
ALTER TABLE session_activities ALTER COLUMN source DROP DEFAULT;
ALTER TABLE session_activities ALTER COLUMN script SET NOT NULL;
ALTER TABLE session_activities ALTER COLUMN rating SET NOT NULL;
