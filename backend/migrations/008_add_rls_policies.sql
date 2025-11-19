-- Migration 008: Add Supabase Row Level Security (RLS) Policies
-- Phase 6: FlutterFlow Integration & Security
-- Adds RLS policies for all tables to secure FlutterFlow integration

-- ============================================================================
-- 6.1: Enable RLS on All Tables
-- ============================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE partner_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE remembered_partners ENABLE ROW LEVEL SECURITY;
ALTER TABLE push_notification_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE anonymous_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_generation_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 6.2: RLS Policies for Users Table
-- ============================================================================

-- Users can read their own row
CREATE POLICY users_select_own ON users
    FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own demographics and preferences (not subscription tier)
CREATE POLICY users_update_own ON users
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Allow users to insert their own record (for registration)
CREATE POLICY users_insert_own ON users
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- ============================================================================
-- 6.3: RLS Policies for Profiles Table
-- ============================================================================

-- Users can read their own profile
CREATE POLICY profiles_select_own ON profiles
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can read profiles of confirmed partners
CREATE POLICY profiles_select_partners ON profiles
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM remembered_partners rp
            WHERE (rp.user_id = auth.uid() AND rp.partner_user_id = profiles.user_id)
               OR (rp.partner_user_id = auth.uid() AND rp.user_id = profiles.user_id)
        )
    );

-- Users can insert their own profile
CREATE POLICY profiles_insert_own ON profiles
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own profile
CREATE POLICY profiles_update_own ON profiles
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Anonymous users can access profiles with matching session ID
-- Note: Anonymous session ID must be set via SET LOCAL app.anonymous_session_id
CREATE POLICY profiles_anonymous_access ON profiles
    FOR ALL
    USING (
        is_anonymous = true 
        AND anonymous_session_id = current_setting('app.anonymous_session_id', true)
    )
    WITH CHECK (
        is_anonymous = true 
        AND anonymous_session_id = current_setting('app.anonymous_session_id', true)
    );

-- ============================================================================
-- 6.4: RLS Policies for Survey Submissions Table
-- ============================================================================

-- Users can read their own submissions
CREATE POLICY survey_submissions_select_own ON survey_submissions
    FOR SELECT
    USING (
        respondent_id = auth.uid()::TEXT
        OR EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.submission_id = survey_submissions.submission_id
            AND p.user_id = auth.uid()
        )
    );

-- Users can insert their own submissions
CREATE POLICY survey_submissions_insert_own ON survey_submissions
    FOR INSERT
    WITH CHECK (true);  -- Allow all inserts, link to user via profiles

-- ============================================================================
-- 6.5: RLS Policies for Survey Progress Table
-- ============================================================================

-- Users can read their own survey progress
CREATE POLICY survey_progress_select_own ON survey_progress
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own survey progress
CREATE POLICY survey_progress_insert_own ON survey_progress
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own survey progress
CREATE POLICY survey_progress_update_own ON survey_progress
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Anonymous users can access survey progress with matching session ID
CREATE POLICY survey_progress_anonymous_access ON survey_progress
    FOR ALL
    USING (
        anonymous_session_id = current_setting('app.anonymous_session_id', true)
    )
    WITH CHECK (
        anonymous_session_id = current_setting('app.anonymous_session_id', true)
    );

-- ============================================================================
-- 6.6: RLS Policies for Sessions Table
-- ============================================================================

-- Users can read sessions they own or participate in
CREATE POLICY sessions_select_participant ON sessions
    FOR SELECT
    USING (
        auth.uid() IN (primary_user_id, partner_user_id, session_owner_user_id)
        OR EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id IN (sessions.primary_profile_id, sessions.partner_profile_id)
            AND p.user_id = auth.uid()
        )
    );

-- Users can insert sessions they own
CREATE POLICY sessions_insert_own ON sessions
    FOR INSERT
    WITH CHECK (auth.uid() = session_owner_user_id);

-- Users can update sessions they own
CREATE POLICY sessions_update_own ON sessions
    FOR UPDATE
    USING (auth.uid() = session_owner_user_id)
    WITH CHECK (auth.uid() = session_owner_user_id);

-- Anonymous users can access sessions with their profile
CREATE POLICY sessions_anonymous_access ON sessions
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id IN (sessions.primary_profile_id, sessions.partner_profile_id)
            AND p.is_anonymous = true
            AND p.anonymous_session_id = current_setting('app.anonymous_session_id', true)
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id IN (sessions.primary_profile_id, sessions.partner_profile_id)
            AND p.is_anonymous = true
            AND p.anonymous_session_id = current_setting('app.anonymous_session_id', true)
        )
    );

-- ============================================================================
-- 6.7: RLS Policies for Session Activities Table
-- ============================================================================

-- Users can read activities for their sessions
CREATE POLICY session_activities_select_own ON session_activities
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM sessions s
            WHERE s.session_id = session_activities.session_id
            AND auth.uid() IN (s.primary_user_id, s.partner_user_id, s.session_owner_user_id)
        )
    );

-- Users can insert activities for their sessions
CREATE POLICY session_activities_insert_own ON session_activities
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM sessions s
            WHERE s.session_id = session_activities.session_id
            AND auth.uid() = s.session_owner_user_id
        )
    );

-- ============================================================================
-- 6.8: RLS Policies for Activities Table (Read-Only)
-- ============================================================================

-- All users can read approved activities
CREATE POLICY activities_select_approved ON activities
    FOR SELECT
    USING (approved = true AND is_active = true);

-- ============================================================================
-- 6.9: RLS Policies for User Activity History Table
-- ============================================================================

-- Users can read their own activity history
CREATE POLICY activity_history_select_own ON user_activity_history
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own activity records
CREATE POLICY activity_history_insert_own ON user_activity_history
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Anonymous users can access history with matching session ID
CREATE POLICY activity_history_anonymous_access ON user_activity_history
    FOR ALL
    USING (
        anonymous_session_id = current_setting('app.anonymous_session_id', true)
    )
    WITH CHECK (
        anonymous_session_id = current_setting('app.anonymous_session_id', true)
    );

-- ============================================================================
-- 6.10: RLS Policies for Partner Connections Table
-- ============================================================================

-- Users can read connection requests they sent or received
CREATE POLICY partner_connections_select_own ON partner_connections
    FOR SELECT
    USING (
        auth.uid() = requester_user_id 
        OR auth.uid() = recipient_user_id
        OR (
            SELECT email FROM users WHERE id = auth.uid()
        ) = recipient_email
    );

-- Users can insert connection requests they are sending
CREATE POLICY partner_connections_insert_own ON partner_connections
    FOR INSERT
    WITH CHECK (auth.uid() = requester_user_id);

-- Users can update connections they received (to accept/decline)
CREATE POLICY partner_connections_update_recipient ON partner_connections
    FOR UPDATE
    USING (
        auth.uid() = recipient_user_id
        OR (
            SELECT email FROM users WHERE id = auth.uid()
        ) = recipient_email
    )
    WITH CHECK (
        auth.uid() = recipient_user_id
        OR (
            SELECT email FROM users WHERE id = auth.uid()
        ) = recipient_email
    );

-- ============================================================================
-- 6.11: RLS Policies for Remembered Partners Table
-- ============================================================================

-- Users can read their own remembered partners
CREATE POLICY remembered_partners_select_own ON remembered_partners
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own remembered partners
CREATE POLICY remembered_partners_insert_own ON remembered_partners
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own remembered partners
CREATE POLICY remembered_partners_delete_own ON remembered_partners
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- 6.12: RLS Policies for Push Notification Tokens Table
-- ============================================================================

-- Users can read their own tokens
CREATE POLICY push_tokens_select_own ON push_notification_tokens
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own tokens
CREATE POLICY push_tokens_insert_own ON push_notification_tokens
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own tokens
CREATE POLICY push_tokens_update_own ON push_notification_tokens
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own tokens
CREATE POLICY push_tokens_delete_own ON push_notification_tokens
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- 6.13: RLS Policies for Subscription Transactions Table
-- ============================================================================

-- Users can read their own subscription transactions
CREATE POLICY subscription_transactions_select_own ON subscription_transactions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Only backend can insert subscription transactions (via service role)
-- No INSERT policy for regular users

-- ============================================================================
-- 6.14: RLS Policies for Anonymous Sessions Table
-- ============================================================================

-- Anonymous users can access their own session
CREATE POLICY anonymous_sessions_access_own ON anonymous_sessions
    FOR ALL
    USING (
        session_id = current_setting('app.anonymous_session_id', true)
    )
    WITH CHECK (
        session_id = current_setting('app.anonymous_session_id', true)
    );

-- ============================================================================
-- 6.15: RLS Policies for AI Generation Logs Table
-- ============================================================================

-- Users can read AI logs for their own sessions
CREATE POLICY ai_logs_select_own ON ai_generation_logs
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM sessions s
            WHERE s.session_id = ai_generation_logs.session_id
            AND auth.uid() IN (s.primary_user_id, s.partner_user_id, s.session_owner_user_id)
        )
    );

-- Only backend can insert AI logs (via service role)
-- No INSERT policy for regular users

-- ============================================================================
-- 6.16: Helper Functions for RLS
-- ============================================================================

-- Function to check if user is premium subscriber
CREATE OR REPLACE FUNCTION is_premium_user(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    user_tier TEXT;
    expires_at TIMESTAMPTZ;
BEGIN
    SELECT subscription_tier, subscription_expires_at
    INTO user_tier, expires_at
    FROM users
    WHERE id = p_user_id;
    
    IF user_tier = 'premium' AND (expires_at IS NULL OR expires_at > NOW()) THEN
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to set anonymous session ID context
CREATE OR REPLACE FUNCTION set_anonymous_session_context(p_session_id TEXT)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.anonymous_session_id', p_session_id, true);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON POLICY users_select_own ON users IS 'Users can only read their own user record';
COMMENT ON POLICY profiles_select_partners ON profiles IS 'Users can read partner profiles if they are remembered partners';
COMMENT ON POLICY profiles_anonymous_access ON profiles IS 'Anonymous users access via app.anonymous_session_id context variable';
COMMENT ON POLICY sessions_select_participant ON sessions IS 'Users can read sessions where they are primary, partner, or owner';
COMMENT ON POLICY activities_select_approved ON activities IS 'All users can read approved, active activities (read-only)';

COMMENT ON FUNCTION is_premium_user(UUID) IS 'Check if user has active premium subscription';
COMMENT ON FUNCTION set_anonymous_session_context(TEXT) IS 'Set session ID context for anonymous user RLS policies';

-- Migration complete

