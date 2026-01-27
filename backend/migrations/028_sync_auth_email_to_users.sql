-- Migration 028: Sync email changes from auth.users to public.users
--
-- Problem: When users change their email via Supabase Auth (e.g., through
-- FlutterFlow), the email is updated in auth.users but NOT in public.users.
-- This causes partner invitations sent to the new email to fail because
-- the lookup queries public.users.email.
--
-- Root Cause: No sync mechanism existed between auth.users and public.users
-- for email updates. User creation was handled by the app calling
-- /api/auth/register, but email changes were not synced.
--
-- Solution: AFTER UPDATE trigger on auth.users that automatically syncs
-- email changes to public.users. Uses SECURITY DEFINER to allow the
-- auth schema trigger to update the public schema.
--
-- Testing: After applying, change a test user's email via Supabase Auth
-- and verify public.users.email is automatically updated.
-- ============================================================================

-- Create the sync function
-- SECURITY DEFINER: Required because this function is called from auth schema
--                   context but needs to update public.users
-- SET search_path = '': Security best practice to prevent search_path attacks
CREATE OR REPLACE FUNCTION public.handle_auth_user_email_update()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    -- Only update if email actually changed and user exists in public.users
    -- Using IS DISTINCT FROM handles NULL safely
    IF NEW.email IS DISTINCT FROM OLD.email THEN
        UPDATE public.users
        SET email = NEW.email
        WHERE id = NEW.id;

        -- Log for debugging (visible in Supabase logs)
        RAISE LOG 'Synced email change for user %: % -> %',
            NEW.id, OLD.email, NEW.email;
    END IF;

    RETURN NEW;
END;
$$;

-- Add comment for documentation
COMMENT ON FUNCTION public.handle_auth_user_email_update() IS
    'Syncs email changes from auth.users to public.users. Called by trigger on auth.users.';

-- Create the trigger on auth.users
-- AFTER UPDATE OF email: Only fires when email column specifically changes
-- This is more efficient than firing on every update
DROP TRIGGER IF EXISTS on_auth_user_email_updated ON auth.users;

CREATE TRIGGER on_auth_user_email_updated
    AFTER UPDATE OF email ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_auth_user_email_update();

-- ============================================================================
-- Migration 028 complete
--
-- Verification steps:
-- 1. Change a test user's email via Supabase Auth dashboard or app
-- 2. Query: SELECT email FROM public.users WHERE id = '<user_id>';
-- 3. Verify the email matches the new value from auth.users
--
-- To check trigger exists:
-- SELECT tgname, tgrelid::regclass, tgenabled
-- FROM pg_trigger
-- WHERE tgname = 'on_auth_user_email_updated';
--
-- To check function exists:
-- SELECT proname, prosecdef, proconfig
-- FROM pg_proc
-- WHERE proname = 'handle_auth_user_email_update';
-- ============================================================================
