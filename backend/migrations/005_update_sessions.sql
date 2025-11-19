-- Migration 005: Update Sessions for MVP Partner Model
-- Phase 3: Session & Game State Management
-- Updates sessions table to support authenticated + anonymous partner combinations

-- ============================================================================
-- 3.1: Create Intimacy Level Enum
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE intimacy_level_enum AS ENUM ('G', 'R', 'X');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- 3.2: Add New Columns to Sessions Table
-- ============================================================================

-- Add primary user fields
ALTER TABLE sessions 
    ADD COLUMN IF NOT EXISTS primary_user_id UUID REFERENCES users(id) ON DELETE SET NULL;  -- NULL if anonymous

ALTER TABLE sessions 
    ADD COLUMN IF NOT EXISTS primary_profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE;  -- Always present

-- Add partner user fields
ALTER TABLE sessions 
    ADD COLUMN IF NOT EXISTS partner_user_id UUID REFERENCES users(id) ON DELETE SET NULL;  -- NULL if anonymous

ALTER TABLE sessions 
    ADD COLUMN IF NOT EXISTS partner_profile_id INTEGER REFERENCES profiles(id) ON DELETE SET NULL;  -- NULL if no survey

-- Add anonymous partner information (FR-47)
ALTER TABLE sessions 
    ADD COLUMN IF NOT EXISTS partner_anonymous_name TEXT;  -- For anonymous partners

ALTER TABLE sessions 
    ADD COLUMN IF NOT EXISTS partner_anonymous_anatomy JSONB;  -- {anatomy_self: [], anatomy_preference: []}

-- Add game configuration
ALTER TABLE sessions 
    ADD COLUMN IF NOT EXISTS intimacy_level intimacy_level_enum NOT NULL DEFAULT 'R';  -- FR-12: G, R, X

ALTER TABLE sessions 
    ADD COLUMN IF NOT EXISTS skip_count INTEGER NOT NULL DEFAULT 0;  -- FR-42: Skip nudge after 3

-- Add session ownership and confirmation
ALTER TABLE sessions 
    ADD COLUMN IF NOT EXISTS session_owner_user_id UUID REFERENCES users(id) ON DELETE SET NULL;  -- Who created session

ALTER TABLE sessions 
    ADD COLUMN IF NOT EXISTS connection_confirmed_at TIMESTAMPTZ;  -- FR-57: When partner confirmed

-- ============================================================================
-- 3.3: Create Indexes for New Columns
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_sessions_primary_user ON sessions(primary_user_id) WHERE primary_user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_primary_profile ON sessions(primary_profile_id);
CREATE INDEX IF NOT EXISTS idx_sessions_partner_user ON sessions(partner_user_id) WHERE partner_user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_partner_profile ON sessions(partner_profile_id) WHERE partner_profile_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_owner ON sessions(session_owner_user_id) WHERE session_owner_user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_intimacy_level ON sessions(intimacy_level);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);

-- ============================================================================
-- 3.4: Data Validation Constraints
-- ============================================================================

-- Validate partner_anonymous_anatomy structure
DO $$ BEGIN
    ALTER TABLE sessions 
      ADD CONSTRAINT chk_sessions_partner_anatomy_structure 
      CHECK (
        partner_anonymous_anatomy IS NULL OR 
        (jsonb_typeof(partner_anonymous_anatomy) = 'object' AND
         partner_anonymous_anatomy ? 'anatomy_self' AND
         partner_anonymous_anatomy ? 'anatomy_preference')
      );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Validate skip_count is non-negative
DO $$ BEGIN
    ALTER TABLE sessions 
      ADD CONSTRAINT chk_sessions_skip_count_positive 
      CHECK (skip_count >= 0);
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- 3.5: Helper Functions
-- ============================================================================

-- Function to get partner profile visibility based on sharing settings
CREATE OR REPLACE FUNCTION get_partner_profile_visibility(
    p_requester_user_id UUID,
    p_partner_user_id UUID
) RETURNS TABLE (
    question_id TEXT,
    answer_value TEXT,
    is_visible BOOLEAN
) AS $$
BEGIN
    -- Get partner's sharing setting
    DECLARE
        partner_sharing_setting TEXT;
    BEGIN
        SELECT u.profile_sharing_setting INTO partner_sharing_setting
        FROM users u
        WHERE u.id = p_partner_user_id;
        
        -- If 'demographics_only', return empty result
        IF partner_sharing_setting = 'demographics_only' THEN
            RETURN;
        END IF;
        
        -- If 'all_responses', return all
        IF partner_sharing_setting = 'all_responses' THEN
            RETURN QUERY
            SELECT 
                key AS question_id,
                value AS answer_value,
                TRUE AS is_visible
            FROM profiles p
            CROSS JOIN LATERAL jsonb_each_text(p.activities)
            WHERE p.user_id = p_partner_user_id;
        END IF;
        
        -- If 'overlapping_only', return only overlapping (both >= 3 on Likert scale)
        -- This is a simplified version - full implementation would need actual Likert scale checks
        RETURN QUERY
        SELECT 
            p2.key AS question_id,
            p2.value AS answer_value,
            TRUE AS is_visible
        FROM profiles pr1
        CROSS JOIN LATERAL jsonb_each_text(pr1.activities) p1
        JOIN profiles pr2 ON pr2.user_id = p_partner_user_id
        CROSS JOIN LATERAL jsonb_each_text(pr2.activities) p2
        WHERE pr1.user_id = p_requester_user_id
        AND p1.key = p2.key
        AND (p1.value::NUMERIC >= 0.5 AND p2.value::NUMERIC >= 0.5);  -- Both neutral or positive
    END;
END;
$$ LANGUAGE plpgsql;

-- Function to reset skip count
CREATE OR REPLACE FUNCTION reset_skip_count_on_activity()
RETURNS TRIGGER AS $$
BEGIN
    -- This would be called when an activity is completed (not skipped)
    -- Implementation would be in application logic, but schema supports it
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 3.6: Backfill Existing Sessions
-- ============================================================================

-- Migrate existing sessions: set player_a as primary, player_b as partner
-- Mark all as anonymous (no user_id) for backward compatibility
UPDATE sessions
SET 
    primary_profile_id = player_a_profile_id,
    partner_profile_id = player_b_profile_id,
    primary_user_id = NULL,  -- Existing sessions are anonymous
    partner_user_id = NULL,
    intimacy_level = 
        CASE 
            WHEN rating = 'G' THEN 'G'::intimacy_level_enum
            WHEN rating = 'X' THEN 'X'::intimacy_level_enum
            ELSE 'R'::intimacy_level_enum
        END
WHERE primary_profile_id IS NULL;  -- Only update rows not yet migrated

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON COLUMN sessions.primary_user_id IS 'Authenticated user playing as primary (NULL if anonymous)';
COMMENT ON COLUMN sessions.primary_profile_id IS 'Profile of primary player (always present)';
COMMENT ON COLUMN sessions.partner_user_id IS 'Authenticated user playing as partner (NULL if anonymous)';
COMMENT ON COLUMN sessions.partner_profile_id IS 'Profile of partner player (NULL if partner has no survey)';
COMMENT ON COLUMN sessions.partner_anonymous_name IS 'Name entered for anonymous partner (FR-47)';
COMMENT ON COLUMN sessions.partner_anonymous_anatomy IS 'Anatomy info for anonymous partner (FR-47)';
COMMENT ON COLUMN sessions.intimacy_level IS 'G=Platonic, R=Exploring, X=Intimate (FR-12)';
COMMENT ON COLUMN sessions.skip_count IS 'Consecutive skips counter for nudge trigger (FR-42)';
COMMENT ON COLUMN sessions.session_owner_user_id IS 'User who created/owns this session';
COMMENT ON COLUMN sessions.connection_confirmed_at IS 'Timestamp when partner confirmed connection (FR-57)';

COMMENT ON TABLE sessions IS 'Game sessions - supports 4 combinations: auth+auth, auth+anon, anon+anon, anon+auth';

-- Migration complete

