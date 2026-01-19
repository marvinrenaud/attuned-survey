-- Migration 020: Add is_read tracking to notifications
-- Enables dynamic badge count and mark-as-read functionality

-- Add is_read column
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE;

-- Add read_at timestamp for when notification was read
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS read_at TIMESTAMPTZ;

-- Partial index for efficient unread notification queries
CREATE INDEX IF NOT EXISTS idx_notifications_unread 
ON notifications(recipient_user_id) 
WHERE is_read = FALSE;

-- Backfill existing notifications as unread
UPDATE notifications SET is_read = FALSE WHERE is_read IS NULL;

-- Comments
COMMENT ON COLUMN notifications.is_read IS 'Whether the notification has been read by the recipient';
COMMENT ON COLUMN notifications.read_at IS 'Timestamp when the notification was marked as read';
