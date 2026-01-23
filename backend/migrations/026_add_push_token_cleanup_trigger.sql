-- Migration 026: Add Push Token Cleanup Trigger
--
-- Problem: FlutterFlow registers FCM tokens via direct Supabase calls:
--   1. DELETE from push_notification_tokens WHERE user_id = X AND platform = Y
--   2. DELETE from push_notification_tokens WHERE device_token = Z
--   3. INSERT new token
--
-- Step 2 fails silently when the device_token belongs to a different user
-- (RLS only allows deleting your own tokens), causing Step 3 to fail with
-- a duplicate key violation.
--
-- Solution: BEFORE INSERT trigger that cleans up conflicting tokens
-- using SECURITY DEFINER to bypass RLS.
-- ============================================================================

-- Create the cleanup function
-- SECURITY DEFINER: runs with the privileges of the function owner (bypasses RLS)
-- SET search_path = '': prevents search_path manipulation attacks
CREATE OR REPLACE FUNCTION public.cleanup_duplicate_device_token()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    -- Delete any existing token with this device_token
    -- This handles the case where a device switches users
    DELETE FROM public.push_notification_tokens
    WHERE device_token = NEW.device_token;

    -- Also delete any existing token for this user+platform combination
    -- This handles the case where a user gets a new token on the same device
    DELETE FROM public.push_notification_tokens
    WHERE user_id = NEW.user_id AND platform = NEW.platform;

    RETURN NEW;
END;
$$;

-- Create the trigger
-- BEFORE INSERT: cleanup happens before the new row is inserted
-- FOR EACH ROW: trigger fires for each row being inserted
DROP TRIGGER IF EXISTS before_insert_push_token ON public.push_notification_tokens;

CREATE TRIGGER before_insert_push_token
    BEFORE INSERT ON public.push_notification_tokens
    FOR EACH ROW
    EXECUTE FUNCTION public.cleanup_duplicate_device_token();

-- ============================================================================
-- Migration 026 complete
--
-- Verification scenario:
-- 1. User A registers device token "ABC123" on iOS → success
-- 2. User A logs out, User B logs in on same device
-- 3. User B tries to register the same device token "ABC123" on iOS
--    → Trigger automatically deletes User A's token
--    → Insert succeeds
-- 4. Query shows token "ABC123" now belongs to User B
-- ============================================================================
