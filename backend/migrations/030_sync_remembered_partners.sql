-- Migration 030: Sync remembered_partners when users update profile
-- Addresses Bug #3: Stale partner data after email/display_name changes
--
-- Problem: When users change their display_name or email, the corresponding
-- entries in remembered_partners are not updated. Partners continue to see
-- outdated information in their "remembered partners" list.
--
-- Solution: AFTER UPDATE triggers on users table that automatically sync
-- changes to remembered_partners. These triggers fire when display_name
-- or email changes and update all related remembered_partners entries.
--
-- Testing: After applying, change a test user's display_name or email and
-- verify all remembered_partners entries with that partner_user_id are updated.
-- ============================================================================

-- ============================================================================
-- 1. sync_remembered_partner_name() - Update partner_name when user changes display_name
-- ============================================================================

CREATE OR REPLACE FUNCTION sync_remembered_partner_name()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    -- Only update if display_name actually changed
    -- Using IS DISTINCT FROM handles NULL safely
    IF OLD.display_name IS DISTINCT FROM NEW.display_name THEN
        UPDATE public.remembered_partners
        SET partner_name = NEW.display_name
        WHERE partner_user_id = NEW.id;

        -- Log for debugging (visible in Supabase logs)
        RAISE LOG 'Synced display_name change to remembered_partners for user %: % -> %',
            NEW.id, OLD.display_name, NEW.display_name;
    END IF;
    RETURN NEW;
END;
$$;

-- Add comment for documentation
COMMENT ON FUNCTION sync_remembered_partner_name() IS
    'Syncs display_name changes from users to remembered_partners.partner_name. Called by trigger on users.';

-- ============================================================================
-- 2. sync_remembered_partner_email() - Update partner_email when user changes email
-- ============================================================================

CREATE OR REPLACE FUNCTION sync_remembered_partner_email()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    -- Only update if email actually changed
    -- Using IS DISTINCT FROM handles NULL safely
    IF OLD.email IS DISTINCT FROM NEW.email THEN
        UPDATE public.remembered_partners
        SET partner_email = NEW.email
        WHERE partner_user_id = NEW.id;

        -- Log for debugging (visible in Supabase logs)
        RAISE LOG 'Synced email change to remembered_partners for user %: % -> %',
            NEW.id, OLD.email, NEW.email;
    END IF;
    RETURN NEW;
END;
$$;

-- Add comment for documentation
COMMENT ON FUNCTION sync_remembered_partner_email() IS
    'Syncs email changes from users to remembered_partners.partner_email. Called by trigger on users.';

-- ============================================================================
-- 3. Create triggers on users table
-- ============================================================================

-- Drop if exists (idempotent)
DROP TRIGGER IF EXISTS trg_sync_remembered_partner_name ON public.users;
DROP TRIGGER IF EXISTS trg_sync_remembered_partner_email ON public.users;

-- Create triggers
-- AFTER UPDATE OF <column>: Only fires when specific column changes (more efficient)
CREATE TRIGGER trg_sync_remembered_partner_name
    AFTER UPDATE OF display_name ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION sync_remembered_partner_name();

CREATE TRIGGER trg_sync_remembered_partner_email
    AFTER UPDATE OF email ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION sync_remembered_partner_email();

-- ============================================================================
-- Migration 030 complete
--
-- Verification steps:
-- 1. Create two test users (A and B)
-- 2. Have user A add user B to remembered_partners
-- 3. Update user B's display_name
-- 4. Query: SELECT partner_name FROM remembered_partners WHERE partner_user_id = '<B_id>';
-- 5. Verify partner_name matches B's new display_name
--
-- To check triggers exist:
-- SELECT tgname, tgrelid::regclass, tgenabled
-- FROM pg_trigger
-- WHERE tgname LIKE 'trg_sync_remembered_partner%';
--
-- To check functions exist:
-- SELECT proname, prosecdef, proconfig
-- FROM pg_proc
-- WHERE proname LIKE 'sync_remembered_partner%';
-- ============================================================================
