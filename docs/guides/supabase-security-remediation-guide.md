# Supabase Security Remediation Guide

This guide walks you through remediating the security and performance issues identified by Supabase Security Advisor and Performance Advisor.

**Date:** 2026-01-21
**Plan Reference:** `docs/plans/2026-01-21-supabase-security-remediation.md`

---

## Prerequisites

- Supabase dashboard access
- The migration files are ready in `backend/migrations/`:
  - `021_fix_function_search_paths.sql`
  - `022_optimize_rls_initplan.sql`

---

## Phase 1: Security Fixes

### Step 1: Enable Leaked Password Protection (Dashboard)

1. Go to **Supabase Dashboard** → **Authentication** → **Settings**
2. Scroll to **Security** section
3. Find **"Enable Leaked Password Protection"** toggle
4. **Enable it** (toggle ON)
5. Click **Save**

This uses HaveIBeenPwned integration to prevent users from registering with known compromised passwords.

---

### Step 2: Fix Function Search Path Security

Open Supabase Dashboard → **SQL Editor** → **New query**

Copy and paste the entire SQL below, then click **Run**:

```sql
-- Migration 021: Fix Function Search Path Security
-- Addresses Supabase Security Advisor warning: "Function Search Path Mutable"
-- Setting search_path to empty string prevents search_path manipulation attacks

-- ============================================================================
-- 1. update_updated_at_column() - Auto-timestamp trigger
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- ============================================================================
-- 2. cleanup_old_anonymous_sessions() - Anonymous session cleanup
-- ============================================================================

-- Must drop first because return type may differ
DROP FUNCTION IF EXISTS cleanup_old_anonymous_sessions(INTEGER);

CREATE OR REPLACE FUNCTION cleanup_old_anonymous_sessions(p_days_old INTEGER DEFAULT 90)
RETURNS TABLE(
    deleted_sessions BIGINT,
    deleted_profiles BIGINT
)
LANGUAGE plpgsql
SET search_path = ''
AS $$
DECLARE
    v_deleted_sessions BIGINT;
    v_deleted_profiles BIGINT;
BEGIN
    -- Delete old anonymous sessions
    WITH deleted AS (
        DELETE FROM public.anonymous_sessions
        WHERE created_at < NOW() - (p_days_old || ' days')::INTERVAL
        RETURNING session_id
    )
    SELECT COUNT(*) INTO v_deleted_sessions FROM deleted;

    -- Delete orphaned anonymous profiles (no matching session)
    WITH deleted AS (
        DELETE FROM public.profiles
        WHERE is_anonymous = true
        AND anonymous_session_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM public.anonymous_sessions a
            WHERE a.session_id = profiles.anonymous_session_id
        )
        RETURNING id
    )
    SELECT COUNT(*) INTO v_deleted_profiles FROM deleted;

    deleted_sessions := v_deleted_sessions;
    deleted_profiles := v_deleted_profiles;
    RETURN NEXT;
END;
$$;

-- ============================================================================
-- 3. survey_progress_set_current_question_index() - Derived column trigger
-- ============================================================================

CREATE OR REPLACE FUNCTION survey_progress_set_current_question_index()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    IF NEW.answers IS NULL THEN
        NEW.current_question_index := NULL;
    ELSIF jsonb_typeof(NEW.answers) = 'array' THEN
        NEW.current_question_index := jsonb_array_length(NEW.answers) + 1;
    ELSIF jsonb_typeof(NEW.answers) = 'object' THEN
        NEW.current_question_index := (SELECT COUNT(*) FROM jsonb_object_keys(NEW.answers)) + 1;
    ELSE
        NEW.current_question_index := 1;
    END IF;
    RETURN NEW;
END;
$$;

-- ============================================================================
-- 4. populate_recipient_name() - Partner connection name sync
-- ============================================================================

CREATE OR REPLACE FUNCTION populate_recipient_name()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    IF NEW.recipient_display_name IS NULL THEN
        IF NEW.recipient_user_id IS NOT NULL THEN
            SELECT display_name INTO NEW.recipient_display_name
            FROM public.users
            WHERE id = NEW.recipient_user_id;
        END IF;

        IF NEW.recipient_display_name IS NULL THEN
            SELECT display_name INTO NEW.recipient_display_name
            FROM public.users
            WHERE email = NEW.recipient_email;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

-- ============================================================================
-- 5. sync_recipient_name_to_connections() - User name change sync
-- ============================================================================

CREATE OR REPLACE FUNCTION sync_recipient_name_to_connections()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    IF OLD.display_name IS DISTINCT FROM NEW.display_name THEN
        UPDATE public.partner_connections
        SET recipient_display_name = NEW.display_name
        WHERE recipient_user_id = NEW.id;

        UPDATE public.partner_connections
        SET recipient_display_name = NEW.display_name
        WHERE recipient_email = NEW.email
        AND recipient_user_id IS NULL;
    END IF;
    RETURN NEW;
END;
$$;

-- ============================================================================
-- 6. populate_requester_name() - Partner connection requester name
-- ============================================================================

CREATE OR REPLACE FUNCTION populate_requester_name()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    IF NEW.requester_display_name IS NULL AND NEW.requester_user_id IS NOT NULL THEN
        SELECT display_name INTO NEW.requester_display_name
        FROM public.users
        WHERE id = NEW.requester_user_id;
    END IF;
    RETURN NEW;
END;
$$;

-- ============================================================================
-- 7. sync_user_name_to_connections() - User name change sync for requester
-- ============================================================================

CREATE OR REPLACE FUNCTION sync_user_name_to_connections()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    IF OLD.display_name IS DISTINCT FROM NEW.display_name THEN
        UPDATE public.partner_connections
        SET requester_display_name = NEW.display_name
        WHERE requester_user_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$;

-- ============================================================================
-- 8. is_premium_user() - Subscription check helper
-- ============================================================================

CREATE OR REPLACE FUNCTION is_premium_user(p_user_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    user_tier TEXT;
    expires_at TIMESTAMPTZ;
BEGIN
    SELECT subscription_tier, subscription_expires_at
    INTO user_tier, expires_at
    FROM public.users
    WHERE id = p_user_id;

    IF user_tier = 'premium' AND (expires_at IS NULL OR expires_at > NOW()) THEN
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$;

-- ============================================================================
-- 9. set_anonymous_session_context() - RLS context helper
-- ============================================================================

CREATE OR REPLACE FUNCTION set_anonymous_session_context(p_session_id TEXT)
RETURNS VOID
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    PERFORM set_config('app.anonymous_session_id', p_session_id, true);
END;
$$;

-- Migration 021 complete
```

**Expected Result:** "Success. No rows returned."

---

## Phase 2: Performance Optimizations

### Step 3: Optimize RLS InitPlan

Open Supabase Dashboard → **SQL Editor** → **New query**

Copy and paste the entire SQL below, then click **Run**:

```sql
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
-- 7. User Activity History Table Policies
-- ============================================================================

DROP POLICY IF EXISTS activity_history_select_own ON user_activity_history;
CREATE POLICY activity_history_select_own ON user_activity_history
    FOR SELECT
    USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS activity_history_insert_own ON user_activity_history;
CREATE POLICY activity_history_insert_own ON user_activity_history
    FOR INSERT
    WITH CHECK ((select auth.uid()) = user_id);

-- ============================================================================
-- 8. Partner Connections Table Policies
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
-- 9. Remembered Partners Table Policies
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
-- 10. Push Notification Tokens Table Policies
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
-- 11. Subscription Transactions Table Policies
-- ============================================================================

DROP POLICY IF EXISTS subscription_transactions_select_own ON subscription_transactions;
CREATE POLICY subscription_transactions_select_own ON subscription_transactions
    FOR SELECT
    USING ((select auth.uid()) = user_id);

-- ============================================================================
-- 12. AI Generation Logs Table Policies
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
```

**Expected Result:** "Success. No rows returned."

---

## Verification

After running both migrations:

1. Go to **Supabase Dashboard** → **Database** → **Functions**
   - Verify functions show `search_path = ''` in their definitions

2. Go to **Supabase Dashboard** → **Authentication** → **Settings**
   - Verify "Leaked Password Protection" is enabled

3. Re-run Supabase Security Advisor and Performance Advisor
   - The "Function Search Path Mutable" warnings should be resolved
   - The "RLS Policies with Inline Auth Calls" warnings should be resolved

---

## Rollback (If Needed)

### Rollback Migration 022 (RLS Optimization)

If you need to revert to the original RLS policies, run the original migration 008 again:

```sql
-- See backend/migrations/008_add_rls_policies.sql for the original policies
```

### Rollback Migration 021 (Function Search Path)

To remove the `search_path` setting from functions, you would need to recreate them without the `SET search_path = ''` clause. This is not recommended as it reintroduces the security vulnerability.

---

## Items NOT Addressed (Intentional)

These warnings were reviewed and determined to be intentional design choices:

| Warning | Reason |
|---------|--------|
| `survey_baseline` RLS disabled | Internal lookup table, no user data |
| Anonymous access policies | Intentional for future anonymous user support |
| `notifications` permissive INSERT/UPDATE | Backend uses service role |
| `compatibility_results` no RLS policies | Table has RLS enabled but accessed only via service role |
| Unindexed foreign keys | Will evaluate after launch based on actual query patterns |

---

## Summary

| Step | Action | Type |
|------|--------|------|
| 1 | Enable Leaked Password Protection | Dashboard |
| 2 | Run Migration 021 | SQL Editor |
| 3 | Run Migration 022 | SQL Editor |

Total estimated time: 5-10 minutes
