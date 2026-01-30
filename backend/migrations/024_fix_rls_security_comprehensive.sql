-- Migration 024: Comprehensive RLS Security Fixes
-- Based on Supabase Security Advisor recommendations and documentation
--
-- This migration addresses:
-- 1. Anonymous Access Warnings - Add "TO authenticated" to user-specific policies
-- 2. Multiple Permissive Policies - Consolidate into single policies with OR conditions
-- 3. Overly Permissive Policies - Remove policies with USING(true) that bypass RLS
-- 4. Security Bug - users_update_own allows bypassing users_update_safe_fields restrictions
--
-- Reference: https://supabase.com/docs/guides/database/postgres/row-level-security

-- ============================================================================
-- PART 1: Remove Overly Permissive Policies (USING true)
-- These bypass RLS security. Service role already bypasses RLS, so these are unnecessary.
-- ============================================================================

-- Remove overly permissive anonymous_sessions policies
DROP POLICY IF EXISTS anonymous_sessions_insert_all ON anonymous_sessions;
DROP POLICY IF EXISTS anonymous_sessions_update_all ON anonymous_sessions;
DROP POLICY IF EXISTS anonymous_sessions_select_all ON anonymous_sessions;

-- Remove overly permissive notifications policies (service role bypasses RLS anyway)
DROP POLICY IF EXISTS notifications_insert_service ON notifications;
DROP POLICY IF EXISTS notifications_update_service ON notifications;

-- ============================================================================
-- PART 2: Fix Users Table - Security Bug & Anonymous Access
-- SECURITY BUG: users_update_own allows bypassing users_update_safe_fields
-- FIX: Remove users_update_own, keep only users_update_safe_fields with TO authenticated
-- ============================================================================

DROP POLICY IF EXISTS users_select_own ON users;
DROP POLICY IF EXISTS users_update_own ON users;
DROP POLICY IF EXISTS users_insert_own ON users;
DROP POLICY IF EXISTS users_update_safe_fields ON users;

-- Users can read their own row (authenticated only)
CREATE POLICY users_select_own ON users
    FOR SELECT
    TO authenticated
    USING ((select auth.uid()) = id);

-- Users can insert their own record (authenticated only, for registration)
CREATE POLICY users_insert_own ON users
    FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) = id);

-- Users can update their own row, but CANNOT modify protected fields
-- Protected: subscription_tier, subscription_expires_at, daily_activity_count, daily_activity_reset_at, created_at
CREATE POLICY users_update_own ON users
    FOR UPDATE
    TO authenticated
    USING ((select auth.uid()) = id)
    WITH CHECK (
        (select auth.uid()) = id
        AND subscription_tier = (SELECT u.subscription_tier FROM users u WHERE u.id = (select auth.uid()))
        AND NOT (subscription_expires_at IS DISTINCT FROM (SELECT u.subscription_expires_at FROM users u WHERE u.id = (select auth.uid())))
        AND daily_activity_count = (SELECT u.daily_activity_count FROM users u WHERE u.id = (select auth.uid()))
        AND NOT (daily_activity_reset_at IS DISTINCT FROM (SELECT u.daily_activity_reset_at FROM users u WHERE u.id = (select auth.uid())))
        AND created_at = (SELECT u.created_at FROM users u WHERE u.id = (select auth.uid()))
    );

-- ============================================================================
-- PART 3: Fix Profiles Table - Consolidate & Add TO authenticated
-- Merge profiles_select_own + profiles_select_partners into single policy
-- ============================================================================

DROP POLICY IF EXISTS profiles_select_own ON profiles;
DROP POLICY IF EXISTS profiles_select_partners ON profiles;
DROP POLICY IF EXISTS profiles_insert_own ON profiles;
DROP POLICY IF EXISTS profiles_update_own ON profiles;

-- Consolidated: Users can read their own profile OR partner profiles (authenticated only)
CREATE POLICY profiles_select ON profiles
    FOR SELECT
    TO authenticated
    USING (
        (select auth.uid()) = user_id
        OR EXISTS (
            SELECT 1 FROM remembered_partners rp
            WHERE (rp.user_id = (select auth.uid()) AND rp.partner_user_id = profiles.user_id)
               OR (rp.partner_user_id = (select auth.uid()) AND rp.user_id = profiles.user_id)
        )
    );

-- Users can insert their own profile (authenticated only)
CREATE POLICY profiles_insert_own ON profiles
    FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) = user_id);

-- Users can update their own profile (authenticated only)
CREATE POLICY profiles_update_own ON profiles
    FOR UPDATE
    TO authenticated
    USING ((select auth.uid()) = user_id)
    WITH CHECK ((select auth.uid()) = user_id);

-- Note: profiles_anonymous_access is kept as-is (intentional for anonymous flow)

-- ============================================================================
-- PART 4: Fix Sessions Table - Consolidate & Add TO authenticated
-- Merge sessions_select_own + sessions_select_participant into single policy
-- ============================================================================

DROP POLICY IF EXISTS sessions_select_own ON sessions;
DROP POLICY IF EXISTS sessions_select_participant ON sessions;
DROP POLICY IF EXISTS sessions_insert_own ON sessions;
DROP POLICY IF EXISTS sessions_update_own ON sessions;

-- Consolidated: Users can read sessions they own or participate in (authenticated only)
CREATE POLICY sessions_select ON sessions
    FOR SELECT
    TO authenticated
    USING (
        (select auth.uid()) IN (primary_user_id, partner_user_id, session_owner_user_id)
        OR EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id IN (sessions.primary_profile_id, sessions.partner_profile_id)
            AND p.user_id = (select auth.uid())
        )
    );

-- Users can insert sessions they own (authenticated only)
CREATE POLICY sessions_insert_own ON sessions
    FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) = session_owner_user_id);

-- Users can update sessions they own (authenticated only)
CREATE POLICY sessions_update_own ON sessions
    FOR UPDATE
    TO authenticated
    USING ((select auth.uid()) = session_owner_user_id)
    WITH CHECK ((select auth.uid()) = session_owner_user_id);

-- Note: sessions_anonymous_access is kept as-is (intentional for anonymous flow)

-- ============================================================================
-- PART 5: Fix Survey Progress - Add TO authenticated
-- ============================================================================

DROP POLICY IF EXISTS survey_progress_select_own ON survey_progress;
DROP POLICY IF EXISTS survey_progress_insert_own ON survey_progress;
DROP POLICY IF EXISTS survey_progress_update_own ON survey_progress;

CREATE POLICY survey_progress_select_own ON survey_progress
    FOR SELECT
    TO authenticated
    USING ((select auth.uid()) = user_id);

CREATE POLICY survey_progress_insert_own ON survey_progress
    FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY survey_progress_update_own ON survey_progress
    FOR UPDATE
    TO authenticated
    USING ((select auth.uid()) = user_id)
    WITH CHECK ((select auth.uid()) = user_id);

-- Note: survey_progress_anonymous_access is kept as-is

-- ============================================================================
-- PART 6: Fix Survey Submissions - Add TO authenticated
-- ============================================================================

DROP POLICY IF EXISTS survey_submissions_select_own ON survey_submissions;
DROP POLICY IF EXISTS survey_submissions_insert_own ON survey_submissions;

CREATE POLICY survey_submissions_select_own ON survey_submissions
    FOR SELECT
    TO authenticated
    USING (
        respondent_id = (select auth.uid())::TEXT
        OR user_id = (select auth.uid())
        OR EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.submission_id = survey_submissions.submission_id
            AND p.user_id = (select auth.uid())
        )
    );

-- Insert policy for authenticated users
CREATE POLICY survey_submissions_insert_own ON survey_submissions
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = (select auth.uid()));

-- ============================================================================
-- PART 7: Fix Session Activities - Add TO authenticated
-- ============================================================================

DROP POLICY IF EXISTS session_activities_select_own ON session_activities;
DROP POLICY IF EXISTS session_activities_insert_own ON session_activities;

CREATE POLICY session_activities_select_own ON session_activities
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM sessions s
            WHERE s.session_id = session_activities.session_id
            AND (select auth.uid()) IN (s.primary_user_id, s.partner_user_id, s.session_owner_user_id)
        )
    );

CREATE POLICY session_activities_insert_own ON session_activities
    FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM sessions s
            WHERE s.session_id = session_activities.session_id
            AND (select auth.uid()) = s.session_owner_user_id
        )
    );

-- ============================================================================
-- PART 8: Fix User Activity History - Add TO authenticated
-- ============================================================================

DROP POLICY IF EXISTS activity_history_select_own ON user_activity_history;
DROP POLICY IF EXISTS activity_history_insert_own ON user_activity_history;

CREATE POLICY activity_history_select_own ON user_activity_history
    FOR SELECT
    TO authenticated
    USING ((select auth.uid()) = user_id);

CREATE POLICY activity_history_insert_own ON user_activity_history
    FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) = user_id);

-- Note: activity_history_anonymous_access is kept as-is

-- ============================================================================
-- PART 9: Fix Partner Connections - Add TO authenticated
-- ============================================================================

DROP POLICY IF EXISTS partner_connections_select_own ON partner_connections;
DROP POLICY IF EXISTS partner_connections_insert_own ON partner_connections;
DROP POLICY IF EXISTS partner_connections_update_recipient ON partner_connections;

CREATE POLICY partner_connections_select_own ON partner_connections
    FOR SELECT
    TO authenticated
    USING (
        (select auth.uid()) = requester_user_id
        OR (select auth.uid()) = recipient_user_id
        OR (SELECT email FROM users WHERE id = (select auth.uid())) = recipient_email
    );

CREATE POLICY partner_connections_insert_own ON partner_connections
    FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) = requester_user_id);

CREATE POLICY partner_connections_update_recipient ON partner_connections
    FOR UPDATE
    TO authenticated
    USING (
        (select auth.uid()) = recipient_user_id
        OR (SELECT email FROM users WHERE id = (select auth.uid())) = recipient_email
    )
    WITH CHECK (
        (select auth.uid()) = recipient_user_id
        OR (SELECT email FROM users WHERE id = (select auth.uid())) = recipient_email
    );

-- ============================================================================
-- PART 10: Fix Remembered Partners - Add TO authenticated
-- ============================================================================

DROP POLICY IF EXISTS remembered_partners_select_own ON remembered_partners;
DROP POLICY IF EXISTS remembered_partners_insert_own ON remembered_partners;
DROP POLICY IF EXISTS remembered_partners_delete_own ON remembered_partners;

CREATE POLICY remembered_partners_select_own ON remembered_partners
    FOR SELECT
    TO authenticated
    USING ((select auth.uid()) = user_id);

CREATE POLICY remembered_partners_insert_own ON remembered_partners
    FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY remembered_partners_delete_own ON remembered_partners
    FOR DELETE
    TO authenticated
    USING ((select auth.uid()) = user_id);

-- ============================================================================
-- PART 11: Fix Push Notification Tokens - Add TO authenticated
-- ============================================================================

DROP POLICY IF EXISTS push_tokens_select_own ON push_notification_tokens;
DROP POLICY IF EXISTS push_tokens_insert_own ON push_notification_tokens;
DROP POLICY IF EXISTS push_tokens_update_own ON push_notification_tokens;
DROP POLICY IF EXISTS push_tokens_delete_own ON push_notification_tokens;

CREATE POLICY push_tokens_select_own ON push_notification_tokens
    FOR SELECT
    TO authenticated
    USING ((select auth.uid()) = user_id);

CREATE POLICY push_tokens_insert_own ON push_notification_tokens
    FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY push_tokens_update_own ON push_notification_tokens
    FOR UPDATE
    TO authenticated
    USING ((select auth.uid()) = user_id)
    WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY push_tokens_delete_own ON push_notification_tokens
    FOR DELETE
    TO authenticated
    USING ((select auth.uid()) = user_id);

-- ============================================================================
-- PART 12: Fix Subscription Transactions - Add TO authenticated
-- ============================================================================

DROP POLICY IF EXISTS subscription_transactions_select_own ON subscription_transactions;

CREATE POLICY subscription_transactions_select_own ON subscription_transactions
    FOR SELECT
    TO authenticated
    USING ((select auth.uid()) = user_id);

-- ============================================================================
-- PART 13: Fix AI Generation Logs - Add TO authenticated
-- ============================================================================

DROP POLICY IF EXISTS ai_logs_select_own ON ai_generation_logs;

CREATE POLICY ai_logs_select_own ON ai_generation_logs
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM sessions s
            WHERE s.session_id = ai_generation_logs.session_id
            AND (select auth.uid()) IN (s.primary_user_id, s.partner_user_id, s.session_owner_user_id)
        )
    );

-- ============================================================================
-- PART 14: Fix Notifications - Add TO authenticated for user select
-- ============================================================================

DROP POLICY IF EXISTS notifications_select_own ON notifications;

CREATE POLICY notifications_select_own ON notifications
    FOR SELECT
    TO authenticated
    USING ((select auth.uid()) = recipient_user_id);

-- Note: No INSERT/UPDATE policies for regular users - backend uses service role

-- ============================================================================
-- Migration 024 complete
--
-- Summary of changes:
-- - Removed 5 overly permissive policies (USING true)
-- - Added TO authenticated to 25+ policies
-- - Consolidated 4 policies into 2 (profiles_select, sessions_select)
-- - Fixed security bug where users_update_own bypassed field restrictions
-- - All policies now use (select auth.uid()) for InitPlan optimization
-- ============================================================================
