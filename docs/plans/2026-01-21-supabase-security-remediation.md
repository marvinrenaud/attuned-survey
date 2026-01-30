# Supabase Security & Performance Remediation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address Supabase Security Advisor warnings by fixing function search_path vulnerabilities and optimizing RLS policy performance.

**Architecture:** Two migrations - one for security (function search_path hardening), one for performance (RLS initplan optimization). Dashboard setting for password protection.

**Tech Stack:** PostgreSQL, Supabase RLS, SQL migrations

---

## Phase 1: Security Hardening

### Task 1.1: Enable Leaked Password Protection (Dashboard)

**This is a manual step in Supabase Dashboard - no code required.**

**Steps:**
1. Go to Supabase Dashboard: https://supabase.com/dashboard
2. Select your project
3. Navigate to **Authentication** → **Providers** → **Email**
4. Scroll to **Password Settings**
5. Enable **"Leaked Password Protection"**
6. Click **Save**

**What this does:** Checks new passwords against HaveIBeenPwned database to prevent users from using compromised passwords.

**Verification:** The warning "Leaked Password Protection Disabled" should disappear from Security Advisor.

---

### Task 1.2: Create Migration for Function Search Path Hardening

**Files:**
- Create: `backend/migrations/021_fix_function_search_paths.sql`
- Create: `backend/migrations/rollback_021.sql`

**Step 1: Create the migration file**

Create `backend/migrations/021_fix_function_search_paths.sql`:

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

-- ============================================================================
-- Note: The following functions reported by Supabase may not exist or are
-- defined elsewhere. If they exist, they should also be updated:
-- - handle_new_submission (webhook trigger - may be inactive)
-- - handle_user_update (webhook trigger - may be inactive)
-- - sync_user_to_profile (not found in codebase)
-- - populate_profile_user_details (not found in codebase)
-- - get_all_app_configs (not found in codebase)
-- ============================================================================

-- Add comments for documentation
COMMENT ON FUNCTION update_updated_at_column() IS 'Auto-update updated_at timestamp on row changes. search_path hardened.';
COMMENT ON FUNCTION cleanup_old_anonymous_sessions(INTEGER) IS 'Delete anonymous sessions older than N days. search_path hardened.';
COMMENT ON FUNCTION survey_progress_set_current_question_index() IS 'Derive question index from answers JSON. search_path hardened.';
```

**Step 2: Create the rollback file**

Create `backend/migrations/rollback_021.sql`:

```sql
-- Rollback 021: Revert Function Search Path Changes
-- Note: This removes the search_path setting but functions remain functional

-- These functions will be recreated by their original migrations if needed
-- Rolling back just removes the search_path hardening

-- The original functions don't have SET search_path, so we recreate without it
-- This is a security downgrade and should only be used if there are issues

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: Full rollback would require recreating all functions without SET search_path
-- For brevity, only the most critical function is shown here.
-- If full rollback is needed, copy original definitions from migrations 003, 007, 008, 011.
```

**Step 3: Verify the migration syntax**

Run: `cd /Users/mr/attuned-survey-1/backend && head -50 migrations/021_fix_function_search_paths.sql`

Expected: See the migration header and first function definition

**Step 4: Commit**

```bash
git add backend/migrations/021_fix_function_search_paths.sql backend/migrations/rollback_021.sql
git commit -m "feat: add migration 021 to fix function search_path security

Addresses Supabase Security Advisor warning 'Function Search Path Mutable'.
Sets search_path = '' on all custom functions to prevent search_path
manipulation attacks."
```

---

### Task 1.3: Apply Migration 021 to Supabase

**This is a manual step in Supabase SQL Editor.**

**Steps:**
1. Go to Supabase Dashboard → SQL Editor
2. Copy the contents of `backend/migrations/021_fix_function_search_paths.sql`
3. Paste into the SQL Editor
4. Click **Run**
5. Verify: "Success. No rows returned" for each statement

**Verification:**
- Go to Security Advisor
- The "Function Search Path Mutable" warnings (12 items) should be reduced or eliminated

**Note:** Some warnings may remain for functions that don't exist in your database or are defined elsewhere (like Supabase internal functions).

---

## Phase 2: Performance Optimization

### Task 2.1: Create Migration for RLS InitPlan Optimization

**Files:**
- Create: `backend/migrations/022_optimize_rls_initplan.sql`
- Create: `backend/migrations/rollback_022.sql`

**Context:** RLS policies using `auth.uid()` directly re-evaluate for each row. Wrapping in `(select auth.uid())` makes it evaluate once per query, significantly improving performance at scale.

**Step 1: Create the migration file**

Create `backend/migrations/022_optimize_rls_initplan.sql`:

```sql
-- Migration 022: Optimize RLS Policies for Performance
-- Addresses Supabase Performance Advisor warning: "Auth RLS Initialization Plan"
-- Wrapping auth.uid() in (select auth.uid()) evaluates once per query instead of per row

-- ============================================================================
-- Strategy: DROP and recreate each policy with optimized auth.uid() calls
-- Using (select auth.uid()) instead of auth.uid() for single evaluation
-- ============================================================================

-- ============================================================================
-- 1. USERS TABLE POLICIES
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

-- users_update_safe_fields (if exists)
DROP POLICY IF EXISTS users_update_safe_fields ON users;
CREATE POLICY users_update_safe_fields ON users
    FOR UPDATE
    USING ((select auth.uid()) = id)
    WITH CHECK ((select auth.uid()) = id);

-- ============================================================================
-- 2. PROFILES TABLE POLICIES
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
-- 3. SURVEY_PROGRESS TABLE POLICIES
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
-- 4. SURVEY_SUBMISSIONS TABLE POLICIES
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

DROP POLICY IF EXISTS survey_submissions_insert_own ON survey_submissions;
CREATE POLICY survey_submissions_insert_own ON survey_submissions
    FOR INSERT
    WITH CHECK (true);  -- Allow all inserts, link to user via profiles

-- ============================================================================
-- 5. SESSIONS TABLE POLICIES
-- ============================================================================

DROP POLICY IF EXISTS sessions_select_own ON sessions;
DROP POLICY IF EXISTS sessions_select_participant ON sessions;
CREATE POLICY sessions_select_own ON sessions
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
-- 6. SESSION_ACTIVITIES TABLE POLICIES
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
-- 7. USER_ACTIVITY_HISTORY TABLE POLICIES
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
-- 8. PARTNER_CONNECTIONS TABLE POLICIES
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
-- 9. REMEMBERED_PARTNERS TABLE POLICIES
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
-- 10. PUSH_NOTIFICATION_TOKENS TABLE POLICIES
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
-- 11. SUBSCRIPTION_TRANSACTIONS TABLE POLICIES
-- ============================================================================

DROP POLICY IF EXISTS subscription_transactions_select_own ON subscription_transactions;
CREATE POLICY subscription_transactions_select_own ON subscription_transactions
    FOR SELECT
    USING ((select auth.uid()) = user_id);

-- ============================================================================
-- 12. AI_GENERATION_LOGS TABLE POLICIES
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

-- ============================================================================
-- 13. NOTIFICATIONS TABLE POLICIES
-- ============================================================================

DROP POLICY IF EXISTS notifications_select_own ON notifications;
CREATE POLICY notifications_select_own ON notifications
    FOR SELECT
    USING ((select auth.uid()) = recipient_user_id);

-- Note: notifications_insert_service and notifications_update_service use (true)
-- and are intentionally permissive for backend service role access

-- ============================================================================
-- Documentation
-- ============================================================================

COMMENT ON POLICY users_select_own ON users IS 'Users read own record. Optimized with (select auth.uid()).';
COMMENT ON POLICY profiles_select_own ON profiles IS 'Users read own profile. Optimized with (select auth.uid()).';
COMMENT ON POLICY sessions_select_own ON sessions IS 'Users read sessions they participate in. Optimized.';
```

**Step 2: Create the rollback file**

Create `backend/migrations/rollback_022.sql`:

```sql
-- Rollback 022: Revert RLS InitPlan Optimizations
-- This reverts to using auth.uid() directly (less performant but functional)
-- Only use if the optimization causes issues

-- Re-run migration 008_add_rls_policies.sql to restore original policies
-- Or selectively recreate policies with auth.uid() instead of (select auth.uid())

-- Example for users table:
DROP POLICY IF EXISTS users_select_own ON users;
CREATE POLICY users_select_own ON users
    FOR SELECT
    USING (auth.uid() = id);

-- For full rollback, re-apply migration 008_add_rls_policies.sql
```

**Step 3: Verify the migration syntax**

Run: `cd /Users/mr/attuned-survey-1/backend && head -60 migrations/022_optimize_rls_initplan.sql`

Expected: See the migration header and first policy definitions

**Step 4: Commit**

```bash
git add backend/migrations/022_optimize_rls_initplan.sql backend/migrations/rollback_022.sql
git commit -m "feat: add migration 022 to optimize RLS policy performance

Addresses Supabase Performance Advisor warning 'Auth RLS Initialization Plan'.
Wraps auth.uid() in (select auth.uid()) so it evaluates once per query
instead of once per row, improving performance at scale."
```

---

### Task 2.2: Apply Migration 022 to Supabase

**This is a manual step in Supabase SQL Editor.**

**Steps:**
1. Go to Supabase Dashboard → SQL Editor
2. Copy the contents of `backend/migrations/022_optimize_rls_initplan.sql`
3. Paste into the SQL Editor
4. Click **Run**
5. Verify: "Success. No rows returned" for each DROP/CREATE statement

**Verification:**
- Go to Performance Advisor
- The "Auth RLS Initialization Plan" warnings (29 items) should be eliminated

**Testing:**
After applying, test that your app still works:
1. Login to your app
2. View your profile
3. Start a game session
4. Verify partner connections list loads

If any issues occur, run `rollback_022.sql` and investigate.

---

## Summary

| Phase | Task | Type | Effort |
|-------|------|------|--------|
| 1 | Enable Leaked Password Protection | Dashboard | 2 min |
| 1 | Create migration 021 (function search_path) | Code | 10 min |
| 1 | Apply migration 021 | Dashboard SQL | 5 min |
| 2 | Create migration 022 (RLS initplan) | Code | 15 min |
| 2 | Apply migration 022 | Dashboard SQL | 5 min |

**Total estimated time:** 30-45 minutes

---

## Post-Remediation Checklist

After completing all tasks:

- [ ] Leaked Password Protection enabled in dashboard
- [ ] Migration 021 applied - function search_path warnings resolved
- [ ] Migration 022 applied - RLS initplan warnings resolved
- [ ] App functionality tested (login, profile, game, partners)
- [ ] Security Advisor shows no ERROR or HIGH warnings
- [ ] Performance Advisor shows reduced warnings
- [ ] Changes committed to git

## Items NOT Addressed (Intentional/Low Priority)

These warnings were evaluated and determined to be intentional design or low priority:

1. **RLS Policy Always True** (anonymous_sessions, notifications) - Intentional for anonymous users and backend service role
2. **Anonymous Access Policies** (19 tables) - Intentional for future anonymous user support
3. **Extension pg_net in Public** - Supabase default, low risk
4. **Unindexed Foreign Keys** (9) - Post-launch optimization
5. **Unused Indexes** (26) - Post-launch cleanup
6. **RLS Disabled on survey_baseline** - Internal table, no user access
