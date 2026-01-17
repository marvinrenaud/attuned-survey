-- Migration 019: Add Notifications Table for Push Notifications
-- Part of push notification backend implementation

-- ============================================================================
-- Create notifications table
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    recipient_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sender_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_sender ON notifications(sender_user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications(sent_at);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);

-- ============================================================================
-- Add unique constraint to push_notification_tokens (user_id + platform)
-- This prevents duplicate registrations for the same user/platform combo
-- First, clean up any existing duplicates by keeping only the most recent
-- ============================================================================

-- Delete older duplicate tokens (keep the one with highest id for each user/platform)
DELETE FROM push_notification_tokens
WHERE id NOT IN (
    SELECT MAX(id)
    FROM push_notification_tokens
    GROUP BY user_id, platform
);

-- Now add the unique constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'push_notification_tokens_user_platform_unique'
    ) THEN
        ALTER TABLE push_notification_tokens 
        ADD CONSTRAINT push_notification_tokens_user_platform_unique 
        UNIQUE (user_id, platform);
    END IF;
END $$;

-- ============================================================================
-- Row Level Security for notifications table
-- ============================================================================

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Users can read their own notifications
CREATE POLICY notifications_select_own ON notifications
    FOR SELECT USING (auth.uid() = recipient_user_id);

-- Service role can insert/update (for backend)
CREATE POLICY notifications_insert_service ON notifications
    FOR INSERT WITH CHECK (true);

CREATE POLICY notifications_update_service ON notifications
    FOR UPDATE USING (true);

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE notifications IS 'Push notification history and queue for FCM delivery';
COMMENT ON COLUMN notifications.recipient_user_id IS 'User who receives the notification';
COMMENT ON COLUMN notifications.sender_user_id IS 'User who triggered the notification (e.g., partner invite sender)';
COMMENT ON COLUMN notifications.notification_type IS 'Type of notification: partner_invitation, invitation_accepted, etc.';
COMMENT ON COLUMN notifications.data IS 'JSON payload for deep linking (initial_page, invitation_id, etc.)';
COMMENT ON COLUMN notifications.sent_at IS 'Timestamp when FCM delivery succeeded (NULL if not yet sent)';

-- Migration complete
