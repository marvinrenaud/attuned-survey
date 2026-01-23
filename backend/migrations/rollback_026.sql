-- Rollback Migration 026: Remove Push Token Cleanup Trigger
-- Run this to undo migration 026

DROP TRIGGER IF EXISTS before_insert_push_token ON public.push_notification_tokens;
DROP FUNCTION IF EXISTS public.cleanup_duplicate_device_token();

-- Rollback 026 complete
