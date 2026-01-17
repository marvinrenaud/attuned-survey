-- Rollback for migration 019: Remove notifications table

DROP POLICY IF EXISTS notifications_update_service ON notifications;
DROP POLICY IF EXISTS notifications_insert_service ON notifications;
DROP POLICY IF EXISTS notifications_select_own ON notifications;

DROP INDEX IF EXISTS idx_notifications_created;
DROP INDEX IF EXISTS idx_notifications_sent_at;
DROP INDEX IF EXISTS idx_notifications_type;
DROP INDEX IF EXISTS idx_notifications_sender;
DROP INDEX IF EXISTS idx_notifications_recipient;

DROP TABLE IF EXISTS notifications;

ALTER TABLE push_notification_tokens 
DROP CONSTRAINT IF EXISTS push_notification_tokens_user_platform_unique;
