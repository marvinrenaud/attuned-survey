-- Rollback for migration 020: Remove is_read tracking

DROP INDEX IF EXISTS idx_notifications_unread;

ALTER TABLE notifications DROP COLUMN IF EXISTS read_at;
ALTER TABLE notifications DROP COLUMN IF EXISTS is_read;
