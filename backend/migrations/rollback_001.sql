-- Rollback migration for activity extensions
-- WARNING: This will result in data loss for the new columns

-- Remove indexes
DROP INDEX IF EXISTS idx_activities_hard_boundaries;
DROP INDEX IF EXISTS idx_activities_required_bodyparts;
DROP INDEX IF EXISTS idx_activities_audience_scope;
DROP INDEX IF EXISTS idx_activities_activity_uid;
DROP INDEX IF EXISTS idx_activities_is_active;
DROP INDEX IF EXISTS idx_activities_active_lookup;

-- Remove constraints
ALTER TABLE activities DROP CONSTRAINT IF EXISTS activities_activity_uid_key;
ALTER TABLE activities DROP CONSTRAINT IF EXISTS chk_hard_boundaries_valid;
ALTER TABLE activities DROP CONSTRAINT IF EXISTS chk_required_bodyparts_structure;

-- Remove columns (data loss!)
ALTER TABLE activities DROP COLUMN IF EXISTS archived_at;
ALTER TABLE activities DROP COLUMN IF EXISTS is_active;
ALTER TABLE activities DROP COLUMN IF EXISTS source_version;
ALTER TABLE activities DROP COLUMN IF EXISTS activity_uid;
ALTER TABLE activities DROP COLUMN IF EXISTS required_bodyparts;
ALTER TABLE activities DROP COLUMN IF EXISTS hard_boundaries;
ALTER TABLE activities DROP COLUMN IF EXISTS audience_scope;

-- Drop enum type
DROP TYPE IF EXISTS audience_scope_enum CASCADE;

-- Remove anatomy column from profiles
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS chk_anatomy_structure;
ALTER TABLE profiles DROP COLUMN IF EXISTS anatomy;

