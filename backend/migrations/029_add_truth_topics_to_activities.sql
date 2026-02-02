-- Migration 029: Add truth_topics column to activities table
--
-- Purpose: Enable filtering of truth activities based on user survey responses
-- for sensitive topics (past_experiences, fantasies, turn_ons, turn_offs,
-- insecurities, boundaries, future_fantasies, feeling_desired).
--
-- The 8 truth topics map to survey questions B29-B36.
-- Users respond Y/M/N which translates to 1.0/0.5/0.0 scores.
-- Activities tagged with truth_topics will be:
--   - Hard filtered if either player said NO (0.0) to any topic
--   - Soft ranked based on YES (1.0) vs MAYBE (0.5) preferences
--   - Activities without truth_topics bypass this filtering entirely
-- ============================================================================

-- Add truth_topics column as JSONB array
ALTER TABLE activities
ADD COLUMN IF NOT EXISTS truth_topics JSONB DEFAULT '[]'::jsonb;

-- Add constraint to ensure it's an array (not object or scalar)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_truth_topics_array'
    ) THEN
        ALTER TABLE activities
        ADD CONSTRAINT chk_truth_topics_array
        CHECK (jsonb_typeof(truth_topics) = 'array');
    END IF;
END $$;

-- Add GIN index for efficient containment queries (e.g., truth_topics @> '["fantasies"]')
CREATE INDEX IF NOT EXISTS idx_activities_truth_topics
ON activities USING GIN (truth_topics);

-- Add comment for documentation
COMMENT ON COLUMN activities.truth_topics IS
'Array of truth topic categories this activity explores. Valid values: past_experiences, fantasies, turn_ons, turn_offs, insecurities, boundaries, future_fantasies, feeling_desired. Empty array means no specific sensitive topics (bypasses truth topic filtering).';

-- ============================================================================
-- Migration 029 complete
-- ============================================================================
