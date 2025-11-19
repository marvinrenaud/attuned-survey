-- Migration 004: Add Partner Connection System
-- Phase 2: Partner & Connection System
-- Adds: partner_connections, remembered_partners, push_notification_tokens tables

-- ============================================================================
-- 2.1: Create Partner Connections Table
-- ============================================================================

-- Create connection status enum
DO $$ BEGIN
    CREATE TYPE connection_status_enum AS ENUM ('pending', 'accepted', 'declined', 'expired');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Create partner_connections table
CREATE TABLE IF NOT EXISTS partner_connections (
    id SERIAL PRIMARY KEY,
    requester_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_email TEXT NOT NULL,
    recipient_user_id UUID REFERENCES users(id) ON DELETE CASCADE,  -- Populated when recipient accepts
    status connection_status_enum NOT NULL DEFAULT 'pending',
    connection_token TEXT UNIQUE NOT NULL,  -- For push notification deep linking
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '5 minutes'),  -- FR-56: 5 minute expiry
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for partner_connections
CREATE INDEX IF NOT EXISTS idx_partner_connections_requester ON partner_connections(requester_user_id);
CREATE INDEX IF NOT EXISTS idx_partner_connections_recipient_email ON partner_connections(recipient_email);
CREATE INDEX IF NOT EXISTS idx_partner_connections_recipient_user ON partner_connections(recipient_user_id) WHERE recipient_user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_partner_connections_status ON partner_connections(status);
CREATE INDEX IF NOT EXISTS idx_partner_connections_token ON partner_connections(connection_token);
CREATE INDEX IF NOT EXISTS idx_partner_connections_expires ON partner_connections(expires_at) WHERE status = 'pending';

-- Create update trigger for partner_connections.updated_at
CREATE TRIGGER update_partner_connections_updated_at BEFORE UPDATE ON partner_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 2.2: Create Remembered Partners Table
-- ============================================================================

-- Create remembered_partners table
CREATE TABLE IF NOT EXISTS remembered_partners (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    partner_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    partner_name TEXT NOT NULL,
    partner_email TEXT NOT NULL,
    last_played_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Unique constraint: can't remember same partner twice
    CONSTRAINT uq_remembered_partners_pair UNIQUE (user_id, partner_user_id),
    
    -- Constraint: can't remember yourself
    CONSTRAINT chk_remembered_partners_not_self CHECK (user_id != partner_user_id)
);

-- Create indexes for remembered_partners
CREATE INDEX IF NOT EXISTS idx_remembered_partners_user ON remembered_partners(user_id);
CREATE INDEX IF NOT EXISTS idx_remembered_partners_partner ON remembered_partners(partner_user_id);
CREATE INDEX IF NOT EXISTS idx_remembered_partners_last_played ON remembered_partners(user_id, last_played_at DESC);

-- ============================================================================
-- 2.3: Create Push Notification Tokens Table
-- ============================================================================

-- Create platform enum
DO $$ BEGIN
    CREATE TYPE platform_enum AS ENUM ('ios', 'android');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Create push_notification_tokens table
CREATE TABLE IF NOT EXISTS push_notification_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_token TEXT UNIQUE NOT NULL,
    platform platform_enum NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for push_notification_tokens
CREATE INDEX IF NOT EXISTS idx_push_tokens_user ON push_notification_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_push_tokens_device ON push_notification_tokens(device_token);
CREATE INDEX IF NOT EXISTS idx_push_tokens_platform ON push_notification_tokens(platform);

-- Create update trigger for push_notification_tokens.updated_at
CREATE TRIGGER update_push_tokens_updated_at BEFORE UPDATE ON push_notification_tokens
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to auto-expire pending connection requests
CREATE OR REPLACE FUNCTION expire_pending_connections()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE partner_connections
    SET status = 'expired'
    WHERE status = 'pending' 
    AND expires_at < NOW();
    
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Function to limit remembered partners to 10 per user (FR-59)
CREATE OR REPLACE FUNCTION enforce_remembered_partners_limit()
RETURNS TRIGGER AS $$
DECLARE
    partner_count INTEGER;
BEGIN
    -- Count current partners for this user
    SELECT COUNT(*) INTO partner_count
    FROM remembered_partners
    WHERE user_id = NEW.user_id;
    
    -- If at or over limit (10), remove oldest partner
    IF partner_count >= 10 THEN
        DELETE FROM remembered_partners
        WHERE id = (
            SELECT id FROM remembered_partners
            WHERE user_id = NEW.user_id
            ORDER BY last_played_at ASC
            LIMIT 1
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to enforce 10-partner limit
CREATE TRIGGER trigger_enforce_remembered_partners_limit
BEFORE INSERT ON remembered_partners
FOR EACH ROW EXECUTE FUNCTION enforce_remembered_partners_limit();

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE partner_connections IS 'Partner connection requests between users';
COMMENT ON COLUMN partner_connections.connection_token IS 'Unique token for deep linking from push notification';
COMMENT ON COLUMN partner_connections.expires_at IS 'Connection request expires after 5 minutes (FR-56)';

COMMENT ON TABLE remembered_partners IS 'Quick reconnect list - max 10 partners per user (FR-59)';
COMMENT ON COLUMN remembered_partners.last_played_at IS 'Last game session timestamp with this partner';

COMMENT ON TABLE push_notification_tokens IS 'Device tokens for push notifications (FCM/APNs)';
COMMENT ON COLUMN push_notification_tokens.device_token IS 'FCM token (Android) or APNs token (iOS)';

-- Migration complete

