-- Migration 035: Enrich JIT activity tracking
-- Purpose: Add columns to session_activities for tracking consumed cards in JIT gameplay
-- This enables session replay, skip tracking, and activity analytics

-- 1. Relax NOT NULL constraints for JIT system compatibility
-- JIT doesn't always have per-card rating string (uses session-level)
ALTER TABLE session_activities ALTER COLUMN rating DROP NOT NULL;

-- JIT fallback cards may lack script content
ALTER TABLE session_activities ALTER COLUMN script DROP NOT NULL;

-- Source should default to 'bank' for normal activities
ALTER TABLE session_activities ALTER COLUMN source SET DEFAULT 'bank';

-- 2. Add new tracking columns

-- Intensity phase from game progression (Warm-up, Build, Peak)
ALTER TABLE session_activities ADD COLUMN IF NOT EXISTS intensity_phase TEXT;

-- Player ID who performed/received the activity
ALTER TABLE session_activities ADD COLUMN IF NOT EXISTS primary_player_id TEXT;

-- Secondary players involved (for group activities)
ALTER TABLE session_activities ADD COLUMN IF NOT EXISTS secondary_player_ids JSONB DEFAULT '[]'::jsonb;

-- Timestamp when card was actually consumed (separate from created_at)
ALTER TABLE session_activities ADD COLUMN IF NOT EXISTS consumed_at TIMESTAMPTZ;

-- Track if this activity was skipped
ALTER TABLE session_activities ADD COLUMN IF NOT EXISTS was_skipped BOOLEAN DEFAULT FALSE;

-- 3. Add index for session replay queries (ordered by consumption time)
CREATE INDEX IF NOT EXISTS idx_session_activities_consumed
  ON session_activities(session_id, consumed_at)
  WHERE consumed_at IS NOT NULL;

-- 4. Add index for skip analytics
CREATE INDEX IF NOT EXISTS idx_session_activities_skipped
  ON session_activities(session_id, was_skipped)
  WHERE was_skipped = TRUE;

COMMENT ON COLUMN session_activities.intensity_phase IS 'Game progression phase: Warm-up, Build, or Peak';
COMMENT ON COLUMN session_activities.primary_player_id IS 'UUID of player who performed the activity';
COMMENT ON COLUMN session_activities.secondary_player_ids IS 'JSON array of secondary player IDs/names';
COMMENT ON COLUMN session_activities.consumed_at IS 'Timestamp when activity was shown to players';
COMMENT ON COLUMN session_activities.was_skipped IS 'True if players skipped this activity';
