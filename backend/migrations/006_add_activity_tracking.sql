-- Migration 006: Add Activity Tracking, AI Logging & Subscriptions
-- Phase 4: Activity Tracking, Monitoring & Subscription
-- Adds: user_activity_history, ai_generation_logs, subscription_transactions tables

-- ============================================================================
-- 4.1: Create User Activity History Table (No-Repeat Logic)
-- ============================================================================

-- Create activity type enum (if not exists)
DO $$ BEGIN
    CREATE TYPE activity_type_enum AS ENUM ('truth', 'dare');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Create feedback type enum
DO $$ BEGIN
    CREATE TYPE feedback_type_enum AS ENUM ('like', 'dislike', 'neutral');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Create user_activity_history table
CREATE TABLE IF NOT EXISTS user_activity_history (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,  -- NULL for anonymous
    anonymous_session_id TEXT,  -- For anonymous users
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    activity_id INTEGER REFERENCES activities(activity_id) ON DELETE SET NULL,
    activity_type activity_type_enum NOT NULL,
    was_skipped BOOLEAN NOT NULL DEFAULT false,
    feedback_type feedback_type_enum,  -- FR-37: User feedback
    feedback_executed BOOLEAN,  -- Did they actually do it?
    presented_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    theme_tags JSONB DEFAULT '[]'::jsonb,  -- For theme diversity tracking (FR-39)
    
    -- Constraint: Either user_id OR anonymous_session_id must be set
    CONSTRAINT chk_activity_history_identity CHECK (
        (user_id IS NOT NULL AND anonymous_session_id IS NULL) OR
        (user_id IS NULL AND anonymous_session_id IS NOT NULL)
    )
);

-- Create indexes for user_activity_history
CREATE INDEX IF NOT EXISTS idx_activity_history_user_presented ON user_activity_history(user_id, presented_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_activity_history_anon_presented ON user_activity_history(anonymous_session_id, presented_at DESC) WHERE anonymous_session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_activity_history_session ON user_activity_history(session_id, presented_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_history_activity ON user_activity_history(activity_id) WHERE activity_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_activity_history_skipped ON user_activity_history(was_skipped);
CREATE INDEX IF NOT EXISTS idx_activity_history_feedback ON user_activity_history(feedback_type) WHERE feedback_type IS NOT NULL;

-- Validate theme_tags structure
DO $$ BEGIN
    ALTER TABLE user_activity_history 
      ADD CONSTRAINT chk_activity_history_theme_tags_structure 
      CHECK (jsonb_typeof(theme_tags) = 'array');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- 4.2: Create AI Generation Logs Table (Monitoring)
-- ============================================================================

-- Create ai_generation_logs table
CREATE TABLE IF NOT EXISTS ai_generation_logs (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT REFERENCES sessions(session_id) ON DELETE CASCADE,
    activity_type activity_type_enum NOT NULL,
    intimacy_level TEXT NOT NULL,
    prompt_text TEXT NOT NULL,  -- Sanitized prompt sent to AI
    response_text TEXT,  -- Raw AI response
    generation_time_ms INTEGER,  -- Latency in milliseconds
    model_version TEXT,  -- e.g., "llama-3.3-70b-versatile"
    was_approved BOOLEAN NOT NULL DEFAULT false,  -- Passed validation?
    validation_failures JSONB,  -- Why rejected: {boundary_violations: [], ...}
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for ai_generation_logs
CREATE INDEX IF NOT EXISTS idx_ai_logs_session ON ai_generation_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_logs_created ON ai_generation_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_logs_approved ON ai_generation_logs(was_approved);
CREATE INDEX IF NOT EXISTS idx_ai_logs_model ON ai_generation_logs(model_version);
CREATE INDEX IF NOT EXISTS idx_ai_logs_generation_time ON ai_generation_logs(generation_time_ms) WHERE generation_time_ms IS NOT NULL;

-- Validate validation_failures structure
DO $$ BEGIN
    ALTER TABLE ai_generation_logs 
      ADD CONSTRAINT chk_ai_logs_validation_structure 
      CHECK (
        validation_failures IS NULL OR 
        jsonb_typeof(validation_failures) = 'object'
      );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- 4.3: Create Subscription Transactions Table
-- ============================================================================

-- Create subscription status enum
DO $$ BEGIN
    CREATE TYPE subscription_status_enum AS ENUM ('active', 'expired', 'canceled', 'refunded');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Create subscription_transactions table
CREATE TABLE IF NOT EXISTS subscription_transactions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform platform_enum NOT NULL,  -- Reuse from migration 004
    platform_transaction_id TEXT UNIQUE NOT NULL,  -- From App Store/Play Store
    subscription_tier TEXT NOT NULL,  -- e.g., "premium", "premium_annual"
    amount DECIMAL(10, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    started_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    auto_renew BOOLEAN NOT NULL DEFAULT true,
    status subscription_status_enum NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for subscription_transactions
CREATE INDEX IF NOT EXISTS idx_subscription_user ON subscription_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_platform_tx ON subscription_transactions(platform_transaction_id);
CREATE INDEX IF NOT EXISTS idx_subscription_status ON subscription_transactions(status);
CREATE INDEX IF NOT EXISTS idx_subscription_expires ON subscription_transactions(expires_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_subscription_created ON subscription_transactions(created_at DESC);

-- Create update trigger for subscription_transactions.updated_at
CREATE TRIGGER update_subscription_transactions_updated_at BEFORE UPDATE ON subscription_transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 4.4: Helper Functions for Activity No-Repeat Logic
-- ============================================================================

-- Function to get activities that should not repeat (FR-31, FR-54)
-- Returns activity IDs to exclude based on:
-- - Presented within 1 year, OR
-- - Less than 100 activities presented since
CREATE OR REPLACE FUNCTION get_excluded_activities_for_user(
    p_user_id UUID DEFAULT NULL,
    p_anonymous_session_id TEXT DEFAULT NULL
) RETURNS TABLE (activity_id INTEGER) AS $$
DECLARE
    one_year_ago TIMESTAMPTZ := NOW() - INTERVAL '1 year';
BEGIN
    IF p_user_id IS NOT NULL THEN
        -- For authenticated users
        RETURN QUERY
        SELECT DISTINCT uah.activity_id
        FROM user_activity_history uah
        WHERE uah.user_id = p_user_id
        AND uah.activity_id IS NOT NULL
        AND (
            -- Within 1 year
            uah.presented_at > one_year_ago
            OR
            -- Less than 100 activities since this one
            (
                SELECT COUNT(*)
                FROM user_activity_history uah2
                WHERE uah2.user_id = p_user_id
                AND uah2.presented_at > uah.presented_at
            ) < 100
        );
    ELSIF p_anonymous_session_id IS NOT NULL THEN
        -- For anonymous users
        RETURN QUERY
        SELECT DISTINCT uah.activity_id
        FROM user_activity_history uah
        WHERE uah.anonymous_session_id = p_anonymous_session_id
        AND uah.activity_id IS NOT NULL
        AND (
            uah.presented_at > one_year_ago
            OR
            (
                SELECT COUNT(*)
                FROM user_activity_history uah2
                WHERE uah2.anonymous_session_id = p_anonymous_session_id
                AND uah2.presented_at > uah.presented_at
            ) < 100
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to check theme diversity (FR-39: max 2 consecutive same theme)
CREATE OR REPLACE FUNCTION check_theme_diversity(
    p_session_id TEXT,
    p_new_theme_tags JSONB
) RETURNS BOOLEAN AS $$
DECLARE
    last_two_themes JSONB[];
    new_primary_theme TEXT;
BEGIN
    -- Get themes from last 2 activities in this session
    SELECT ARRAY_AGG(theme_tags ORDER BY presented_at DESC)
    INTO last_two_themes
    FROM (
        SELECT theme_tags, presented_at
        FROM user_activity_history
        WHERE session_id = p_session_id
        ORDER BY presented_at DESC
        LIMIT 2
    ) recent;
    
    -- If less than 2 previous activities, allow any theme
    IF array_length(last_two_themes, 1) < 2 THEN
        RETURN TRUE;
    END IF;
    
    -- Extract primary theme from new activity (first element of array)
    SELECT theme_tags->0 INTO new_primary_theme
    FROM jsonb_array_elements_text(p_new_theme_tags) theme_tags
    LIMIT 1;
    
    -- Check if both previous activities have same primary theme as new one
    -- If so, reject (max 2 consecutive)
    IF (last_two_themes[1]->0)::TEXT = new_primary_theme 
       AND (last_two_themes[2]->0)::TEXT = new_primary_theme THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to reset daily activity count (called by cron job)
CREATE OR REPLACE FUNCTION reset_daily_activity_counts()
RETURNS INTEGER AS $$
DECLARE
    reset_count INTEGER;
BEGIN
    UPDATE users
    SET 
        daily_activity_count = 0,
        daily_activity_reset_at = NOW()
    WHERE daily_activity_reset_at < NOW() - INTERVAL '1 day';
    
    GET DIAGNOSTICS reset_count = ROW_COUNT;
    RETURN reset_count;
END;
$$ LANGUAGE plpgsql;

-- Function to check if user has reached daily limit (FR-25)
CREATE OR REPLACE FUNCTION check_daily_activity_limit(
    p_user_id UUID,
    p_daily_limit INTEGER DEFAULT 25
) RETURNS BOOLEAN AS $$
DECLARE
    user_tier TEXT;
    activity_count INTEGER;
BEGIN
    -- Get user's subscription tier
    SELECT subscription_tier INTO user_tier
    FROM users
    WHERE id = p_user_id;
    
    -- Premium users have no limit
    IF user_tier = 'premium' THEN
        RETURN TRUE;
    END IF;
    
    -- Check if count needs reset
    PERFORM 1 FROM users
    WHERE id = p_user_id
    AND daily_activity_reset_at < NOW() - INTERVAL '1 day';
    
    IF FOUND THEN
        UPDATE users
        SET daily_activity_count = 0,
            daily_activity_reset_at = NOW()
        WHERE id = p_user_id;
    END IF;
    
    -- Check current count
    SELECT daily_activity_count INTO activity_count
    FROM users
    WHERE id = p_user_id;
    
    RETURN activity_count < p_daily_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE user_activity_history IS 'Complete history of activities presented to users (FR-30)';
COMMENT ON COLUMN user_activity_history.was_skipped IS 'True if user skipped this activity (FR-13)';
COMMENT ON COLUMN user_activity_history.feedback_type IS 'User feedback: like, dislike, neutral (FR-37)';
COMMENT ON COLUMN user_activity_history.feedback_executed IS 'Did user actually perform the activity? (FR-37)';
COMMENT ON COLUMN user_activity_history.theme_tags IS 'Activity themes for diversity tracking (FR-39)';

COMMENT ON TABLE ai_generation_logs IS 'Logs of AI-generated activities for monitoring and improvement';
COMMENT ON COLUMN ai_generation_logs.generation_time_ms IS 'AI response latency in milliseconds';
COMMENT ON COLUMN ai_generation_logs.was_approved IS 'True if activity passed validation and was presented';
COMMENT ON COLUMN ai_generation_logs.validation_failures IS 'Reasons activity was rejected (boundary violations, etc.)';

COMMENT ON TABLE subscription_transactions IS 'Purchase records from App Store and Play Store (FR-26)';
COMMENT ON COLUMN subscription_transactions.platform_transaction_id IS 'Unique transaction ID from platform (for webhook validation)';
COMMENT ON COLUMN subscription_transactions.auto_renew IS 'Whether subscription will auto-renew';

-- Migration complete

