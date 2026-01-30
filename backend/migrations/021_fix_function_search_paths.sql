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
