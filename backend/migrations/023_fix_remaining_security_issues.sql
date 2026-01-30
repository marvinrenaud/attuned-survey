-- Migration 023: Fix Remaining Security and Performance Issues
-- Addresses remaining Supabase Security Advisor and Performance Advisor warnings
--
-- Part 1: Functions missing search_path (5 functions)
-- Part 2: Policies needing InitPlan optimization (4 policies)

-- ============================================================================
-- PART 1: Fix Function Search Path Security
-- ============================================================================

-- 1. get_all_app_configs() - App config helper (SECURITY DEFINER)
CREATE OR REPLACE FUNCTION public.get_all_app_configs()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
BEGIN
    RETURN (SELECT jsonb_object_agg(key, value) FROM public.app_config);
END;
$function$;

-- 2. populate_profile_user_details() - Profile trigger
CREATE OR REPLACE FUNCTION public.populate_profile_user_details()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $function$
BEGIN
    IF NEW.user_id IS NOT NULL THEN
        SELECT display_name, email
        INTO NEW.display_name, NEW.email
        FROM public.users
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$function$;

-- 3. sync_user_to_profile() - User sync trigger
CREATE OR REPLACE FUNCTION public.sync_user_to_profile()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $function$
BEGIN
    UPDATE public.profiles
    SET display_name = NEW.display_name,
        email = NEW.email
    WHERE user_id = NEW.id;
    RETURN NEW;
END;
$function$;

-- 4. handle_new_submission() - Survey submission webhook trigger
CREATE OR REPLACE FUNCTION public.handle_new_submission()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
DECLARE
  backend_url text := 'https://attuned-backend.onrender.com';
BEGIN
  PERFORM net.http_post(
    url := backend_url || '/api/survey/submissions/' || new.submission_id || '/process',
    body := '{}'::jsonb
  );
  RETURN new;
END;
$$;

-- 5. handle_user_update() - User anatomy sync trigger
CREATE OR REPLACE FUNCTION public.handle_user_update()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
DECLARE
  backend_url text := 'https://attuned-backend.onrender.com';
BEGIN
  IF (old.has_penis IS DISTINCT FROM new.has_penis) OR
     (old.has_vagina IS DISTINCT FROM new.has_vagina) OR
     (old.has_breasts IS DISTINCT FROM new.has_breasts) OR
     (old.likes_penis IS DISTINCT FROM new.likes_penis) OR
     (old.likes_vagina IS DISTINCT FROM new.likes_vagina) OR
     (old.likes_breasts IS DISTINCT FROM new.likes_breasts) THEN

      PERFORM net.http_post(
        url := backend_url || '/api/users/' || new.id || '/sync',
        body := '{}'::jsonb
      );

  END IF;
  RETURN new;
END;
$$;

-- ============================================================================
-- PART 2: Fix RLS InitPlan Performance
-- ============================================================================

-- 1. sessions_select_own - Optimized with (select auth.uid())
DROP POLICY IF EXISTS sessions_select_own ON sessions;
CREATE POLICY sessions_select_own ON sessions
    FOR SELECT
    USING ((select auth.uid()) IN (primary_user_id, partner_user_id, session_owner_user_id));

-- 2. survey_submissions_insert_own - Optimized with (select auth.uid())
DROP POLICY IF EXISTS survey_submissions_insert_own ON survey_submissions;
CREATE POLICY survey_submissions_insert_own ON survey_submissions
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = (select auth.uid()));

-- 3. notifications_select_own - Optimized with (select auth.uid())
DROP POLICY IF EXISTS notifications_select_own ON notifications;
CREATE POLICY notifications_select_own ON notifications
    FOR SELECT
    USING ((select auth.uid()) = recipient_user_id);

-- 4. users_update_safe_fields - Optimized with (select auth.uid())
-- This policy prevents users from modifying protected fields:
-- subscription_tier, subscription_expires_at, daily_activity_count, daily_activity_reset_at, created_at
DROP POLICY IF EXISTS users_update_safe_fields ON users;
CREATE POLICY users_update_safe_fields ON users
    FOR UPDATE
    USING ((select auth.uid()) = id)
    WITH CHECK (
        (select auth.uid()) = id
        AND subscription_tier = (SELECT u.subscription_tier FROM users u WHERE u.id = (select auth.uid()))
        AND NOT (subscription_expires_at IS DISTINCT FROM (SELECT u.subscription_expires_at FROM users u WHERE u.id = (select auth.uid())))
        AND daily_activity_count = (SELECT u.daily_activity_count FROM users u WHERE u.id = (select auth.uid()))
        AND NOT (daily_activity_reset_at IS DISTINCT FROM (SELECT u.daily_activity_reset_at FROM users u WHERE u.id = (select auth.uid())))
        AND created_at = (SELECT u.created_at FROM users u WHERE u.id = (select auth.uid()))
    );

-- Migration 023 complete
