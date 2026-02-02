-- Rollback Migration 029: Remove truth_topics column from activities table
-- ============================================================================

DROP INDEX IF EXISTS idx_activities_truth_topics;

ALTER TABLE activities DROP CONSTRAINT IF EXISTS chk_truth_topics_array;

ALTER TABLE activities DROP COLUMN IF EXISTS truth_topics;

-- ============================================================================
-- Rollback 029 complete
-- ============================================================================
