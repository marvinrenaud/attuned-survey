-- Migration 022: Optimize RLS Policies with InitPlan
-- Addresses Supabase Performance Advisor warning: "RLS Policies with Inline Auth Calls"
-- Using (select auth.uid()) instead of auth.uid() evaluates once per query, not per row

-- ============================================================================
-- 1. Users Table Policies
-- ============================================================================

DROP POLICY IF EXISTS users_select_own ON users;
CREATE POLICY users_select_own ON users
    FOR SELECT
    USING ((select auth.uid()) = id);

DROP POLICY IF EXISTS users_update_own ON users;
CREATE POLICY users_update_own ON users
    FOR UPDATE
    USING ((select auth.uid()) = id)
    WITH CHECK ((select auth.uid()) = id);

DROP POLICY IF EXISTS users_insert_own ON users;
CREATE POLICY users_insert_own ON users
    FOR INSERT
    WITH CHECK ((select auth.uid()) = id);

-- ============================================================================
-- 2. Profiles Table Policies
-- ============================================================================

DROP POLICY IF EXISTS profiles_select_own ON profiles;
CREATE POLICY profiles_select_own ON profiles
    FOR SELECT
    USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS profiles_select_partners ON profiles;
CREATE POLICY profiles_select_partners ON profiles
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM remembered_partners rp
            WHERE (rp.user_id = (select auth.uid()) AND rp.partner_user_id = profiles.user_id)
               OR (rp.partner_user_id = (select auth.uid()) AND rp.user_id = profiles.user_id)
        )
    );

DROP POLICY IF EXISTS profiles_insert_own ON profiles;
CREATE POLICY profiles_insert_own ON profiles
    FOR INSERT
    WITH CHECK ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS profiles_update_own ON profiles;
CREATE POLICY profiles_update_own ON profiles
    FOR UPDATE
    USING ((select auth.uid()) = user_id)
    WITH CHECK ((select auth.uid()) = user_id);

-- Note: profiles_anonymous_access uses current_setting(), not auth.uid() - no change needed

-- ============================================================================
-- 3. Survey Submissions Table Policies
-- ============================================================================

DROP POLICY IF EXISTS survey_submissions_select_own ON survey_submissions;
CREATE POLICY survey_submissions_select_own ON survey_submissions
    FOR SELECT
    USING (
        respondent_id = (select auth.uid())::TEXT
        OR EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.submission_id = survey_submissions.submission_id
            AND p.user_id = (select auth.uid())
        )
    );

-- Note: survey_submissions_insert_own uses WITH CHECK (true) - no auth.uid() to optimize

-- ============================================================================
-- 4. Survey Progress Table Policies
-- ============================================================================

DROP POLICY IF EXISTS survey_progress_select_own ON survey_progress;
CREATE POLICY survey_progress_select_own ON survey_progress
    FOR SELECT
    USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS survey_progress_insert_own ON survey_progress;
CREATE POLICY survey_progress_insert_own ON survey_progress
    FOR INSERT
    WITH CHECK ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS survey_progress_update_own ON survey_progress;
CREATE POLICY survey_progress_update_own ON survey_progress
    FOR UPDATE
    USING ((select auth.uid()) = user_id)
    WITH CHECK ((select auth.uid()) = user_id);

-- Note: survey_progress_anonymous_access uses current_setting() - no change needed

-- ============================================================================
-- 5. Sessions Table Policies
-- ============================================================================

DROP POLICY IF EXISTS sessions_select_participant ON sessions;
CREATE POLICY sessions_select_participant ON sessions
    FOR SELECT
    USING (
        (select auth.uid()) IN (primary_user_id, partner_user_id, session_owner_user_id)
        OR EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id IN (sessions.primary_profile_id, sessions.partner_profile_id)
            AND p.user_id = (select auth.uid())
        )
    );

DROP POLICY IF EXISTS sessions_insert_own ON sessions;
CREATE POLICY sessions_insert_own ON sessions
    FOR INSERT
    WITH CHECK ((select auth.uid()) = session_owner_user_id);

DROP POLICY IF EXISTS sessions_update_own ON sessions;
CREATE POLICY sessions_update_own ON sessions
    FOR UPDATE
    USING ((select auth.uid()) = session_owner_user_id)
    WITH CHECK ((select auth.uid()) = session_owner_user_id);

-- Note: sessions_anonymous_access uses current_setting() - no change needed

-- ============================================================================
-- 6. Session Activities Table Policies
-- ============================================================================

DROP POLICY IF EXISTS session_activities_select_own ON session_activities;
CREATE POLICY session_activities_select_own ON session_activities
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM sessions s
            WHERE s.session_id = session_activities.session_id
            AND (select auth.uid()) IN (s.primary_user_id, s.partner_user_id, s.session_owner_user_id)
        )
    );

DROP POLICY IF EXISTS session_activities_insert_own ON session_activities;
CREATE POLICY session_activities_insert_own ON session_activities
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM sessions s
            WHERE s.session_id = session_activities.session_id
            AND (select auth.uid()) = s.session_owner_user_id
        )
    );

-- ============================================================================
-- 7. Activities Table Policies (No change needed)
-- ============================================================================
-- activities_select_approved doesn't use auth.uid()

-- ============================================================================
-- 8. User Activity History Table Policies
-- ============================================================================

DROP POLICY IF EXISTS activity_history_select_own ON user_activity_history;
CREATE POLICY activity_history_select_own ON user_activity_history
    FOR SELECT
    USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS activity_history_insert_own ON user_activity_history;
CREATE POLICY activity_history_insert_own ON user_activity_history
    FOR INSERT
    WITH CHECK ((select auth.uid()) = user_id);

-- Note: activity_history_anonymous_access uses current_setting() - no change needed

-- ============================================================================
-- 9. Partner Connections Table Policies
-- ============================================================================

DROP POLICY IF EXISTS partner_connections_select_own ON partner_connections;
CREATE POLICY partner_connections_select_own ON partner_connections
    FOR SELECT
    USING (
        (select auth.uid()) = requester_user_id
        OR (select auth.uid()) = recipient_user_id
        OR (
            SELECT email FROM users WHERE id = (select auth.uid())
        ) = recipient_email
    );

DROP POLICY IF EXISTS partner_connections_insert_own ON partner_connections;
CREATE POLICY partner_connections_insert_own ON partner_connections
    FOR INSERT
    WITH CHECK ((select auth.uid()) = requester_user_id);

DROP POLICY IF EXISTS partner_connections_update_recipient ON partner_connections;
CREATE POLICY partner_connections_update_recipient ON partner_connections
    FOR UPDATE
    USING (
        (select auth.uid()) = recipient_user_id
        OR (
            SELECT email FROM users WHERE id = (select auth.uid())
        ) = recipient_email
    )
    WITH CHECK (
        (select auth.uid()) = recipient_user_id
        OR (
            SELECT email FROM users WHERE id = (select auth.uid())
        ) = recipient_email
    );

-- ============================================================================
-- 10. Remembered Partners Table Policies
-- ============================================================================

DROP POLICY IF EXISTS remembered_partners_select_own ON remembered_partners;
CREATE POLICY remembered_partners_select_own ON remembered_partners
    FOR SELECT
    USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS remembered_partners_insert_own ON remembered_partners;
CREATE POLICY remembered_partners_insert_own ON remembered_partners
    FOR INSERT
    WITH CHECK ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS remembered_partners_delete_own ON remembered_partners;
CREATE POLICY remembered_partners_delete_own ON remembered_partners
    FOR DELETE
    USING ((select auth.uid()) = user_id);

-- ============================================================================
-- 11. Push Notification Tokens Table Policies
-- ============================================================================

DROP POLICY IF EXISTS push_tokens_select_own ON push_notification_tokens;
CREATE POLICY push_tokens_select_own ON push_notification_tokens
    FOR SELECT
    USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS push_tokens_insert_own ON push_notification_tokens;
CREATE POLICY push_tokens_insert_own ON push_notification_tokens
    FOR INSERT
    WITH CHECK ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS push_tokens_update_own ON push_notification_tokens;
CREATE POLICY push_tokens_update_own ON push_notification_tokens
    FOR UPDATE
    USING ((select auth.uid()) = user_id)
    WITH CHECK ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS push_tokens_delete_own ON push_notification_tokens;
CREATE POLICY push_tokens_delete_own ON push_notification_tokens
    FOR DELETE
    USING ((select auth.uid()) = user_id);

-- ============================================================================
-- 12. Subscription Transactions Table Policies
-- ============================================================================

DROP POLICY IF EXISTS subscription_transactions_select_own ON subscription_transactions;
CREATE POLICY subscription_transactions_select_own ON subscription_transactions
    FOR SELECT
    USING ((select auth.uid()) = user_id);

-- ============================================================================
-- 13. AI Generation Logs Table Policies
-- ============================================================================

DROP POLICY IF EXISTS ai_logs_select_own ON ai_generation_logs;
CREATE POLICY ai_logs_select_own ON ai_generation_logs
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM sessions s
            WHERE s.session_id = ai_generation_logs.session_id
            AND (select auth.uid()) IN (s.primary_user_id, s.partner_user_id, s.session_owner_user_id)
        )
    );

-- Migration 022 complete
-- Total policies optimized: 29
