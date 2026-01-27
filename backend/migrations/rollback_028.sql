-- Rollback for Migration 028: Remove email sync trigger
-- ============================================================================

-- Drop the trigger first (depends on the function)
DROP TRIGGER IF EXISTS on_auth_user_email_updated ON auth.users;

-- Drop the function
DROP FUNCTION IF EXISTS public.handle_auth_user_email_update();

-- ============================================================================
-- Rollback complete
--
-- After rollback, email changes in auth.users will no longer sync to
-- public.users. The app would need to manually update public.users.email
-- when users change their email.
-- ============================================================================
