-- Migration 007: Add Anonymous User Management
-- Phase 5: Anonymous User Management
-- Adds: anonymous_sessions table with cleanup policy

-- ============================================================================
-- 5.1: Create Anonymous Sessions Table
-- ============================================================================

-- Create anonymous_sessions table
CREATE TABLE IF NOT EXISTS anonymous_sessions (
    session_id TEXT PRIMARY KEY,  -- UUID generated client-side, stored in local storage
    profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE,  -- Linked anonymous profile
    device_fingerprint JSONB,  -- For multi-device detection (optional)
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for anonymous_sessions
CREATE INDEX IF NOT EXISTS idx_anonymous_sessions_profile ON anonymous_sessions(profile_id);
CREATE INDEX IF NOT EXISTS idx_anonymous_sessions_last_accessed ON anonymous_sessions(last_accessed_at);
CREATE INDEX IF NOT EXISTS idx_anonymous_sessions_created ON anonymous_sessions(created_at);

-- Validate device_fingerprint structure
DO $$ BEGIN
    ALTER TABLE anonymous_sessions 
      ADD CONSTRAINT chk_anonymous_sessions_fingerprint_structure 
      CHECK (
        device_fingerprint IS NULL OR 
        jsonb_typeof(device_fingerprint) = 'object'
      );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- 5.2: Cleanup Functions for Old Anonymous Data
-- ============================================================================

-- Function to clean up anonymous sessions older than 90 days
CREATE OR REPLACE FUNCTION cleanup_old_anonymous_sessions(
    p_days_old INTEGER DEFAULT 90
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
    cutoff_date TIMESTAMPTZ := NOW() - (p_days_old || ' days')::INTERVAL;
BEGIN
    -- Delete anonymous sessions older than threshold
    DELETE FROM anonymous_sessions
    WHERE last_accessed_at < cutoff_date;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Also clean up orphaned anonymous profiles
    DELETE FROM profiles
    WHERE is_anonymous = true
    AND last_accessed_at < cutoff_date
    AND id NOT IN (SELECT profile_id FROM anonymous_sessions WHERE profile_id IS NOT NULL);
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update last_accessed_at on anonymous session
CREATE OR REPLACE FUNCTION touch_anonymous_session(
    p_session_id TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE anonymous_sessions
    SET last_accessed_at = NOW()
    WHERE session_id = p_session_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to link anonymous profile to session
CREATE OR REPLACE FUNCTION link_anonymous_profile_to_session(
    p_session_id TEXT,
    p_profile_id INTEGER
) RETURNS BOOLEAN AS $$
BEGIN
    -- Create or update anonymous session
    INSERT INTO anonymous_sessions (session_id, profile_id, last_accessed_at)
    VALUES (p_session_id, p_profile_id, NOW())
    ON CONFLICT (session_id) 
    DO UPDATE SET 
        profile_id = EXCLUDED.profile_id,
        last_accessed_at = NOW();
    
    -- Update profile's anonymous_session_id
    UPDATE profiles
    SET 
        anonymous_session_id = p_session_id,
        last_accessed_at = NOW()
    WHERE id = p_profile_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5.3: Helper Views for Anonymous User Management
-- ============================================================================

-- View to get anonymous sessions that are due for cleanup
CREATE OR REPLACE VIEW anonymous_sessions_to_cleanup AS
SELECT 
    as_table.session_id,
    as_table.profile_id,
    as_table.last_accessed_at,
    as_table.created_at,
    EXTRACT(DAY FROM NOW() - as_table.last_accessed_at) AS days_inactive
FROM anonymous_sessions as_table
WHERE as_table.last_accessed_at < NOW() - INTERVAL '90 days';

-- View to get statistics on anonymous usage
CREATE OR REPLACE VIEW anonymous_session_stats AS
SELECT 
    COUNT(*) AS total_sessions,
    COUNT(DISTINCT profile_id) AS profiles_with_sessions,
    AVG(EXTRACT(DAY FROM NOW() - last_accessed_at)) AS avg_days_since_access,
    MIN(last_accessed_at) AS oldest_access,
    MAX(last_accessed_at) AS newest_access,
    COUNT(*) FILTER (WHERE last_accessed_at < NOW() - INTERVAL '90 days') AS sessions_due_for_cleanup
FROM anonymous_sessions;

-- ============================================================================
-- 5.4: Trigger to Auto-Update last_accessed_at
-- ============================================================================

-- Trigger function to update last_accessed_at on profile access
CREATE OR REPLACE FUNCTION update_anonymous_profile_access()
RETURNS TRIGGER AS $$
BEGIN
    -- Update corresponding anonymous session
    UPDATE anonymous_sessions
    SET last_accessed_at = NOW()
    WHERE profile_id = NEW.id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on profiles table for anonymous profiles
CREATE TRIGGER trigger_update_anonymous_profile_access
AFTER UPDATE ON profiles
FOR EACH ROW
WHEN (NEW.is_anonymous = true)
EXECUTE FUNCTION update_anonymous_profile_access();

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE anonymous_sessions IS 'Tracks anonymous user sessions for profile persistence (FR-08, FR-46)';
COMMENT ON COLUMN anonymous_sessions.session_id IS 'UUID from client local storage - PRIMARY KEY';
COMMENT ON COLUMN anonymous_sessions.profile_id IS 'Linked profile for this anonymous user';
COMMENT ON COLUMN anonymous_sessions.device_fingerprint IS 'Optional device info for multi-device detection';
COMMENT ON COLUMN anonymous_sessions.last_accessed_at IS 'Last activity timestamp (used for 90-day cleanup)';

COMMENT ON FUNCTION cleanup_old_anonymous_sessions(INTEGER) IS 'Delete anonymous sessions older than specified days (default 90)';
COMMENT ON FUNCTION touch_anonymous_session(TEXT) IS 'Update last_accessed_at for an anonymous session';
COMMENT ON FUNCTION link_anonymous_profile_to_session(TEXT, INTEGER) IS 'Link a profile to an anonymous session';

COMMENT ON VIEW anonymous_sessions_to_cleanup IS 'Anonymous sessions older than 90 days ready for deletion';
COMMENT ON VIEW anonymous_session_stats IS 'Statistics on anonymous session usage';

-- Migration complete

