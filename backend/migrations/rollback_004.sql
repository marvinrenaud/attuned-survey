-- Rollback Migration 004: Remove Partner Connection System
-- Reverses all changes from 004_add_partner_system.sql

-- Drop triggers
DROP TRIGGER IF EXISTS trigger_enforce_remembered_partners_limit ON remembered_partners;
DROP TRIGGER IF EXISTS update_push_tokens_updated_at ON push_notification_tokens;
DROP TRIGGER IF EXISTS update_partner_connections_updated_at ON partner_connections;

-- Drop functions
DROP FUNCTION IF EXISTS enforce_remembered_partners_limit();
DROP FUNCTION IF EXISTS expire_pending_connections();

-- Drop indexes and tables for push_notification_tokens
DROP INDEX IF EXISTS idx_push_tokens_platform;
DROP INDEX IF EXISTS idx_push_tokens_device;
DROP INDEX IF EXISTS idx_push_tokens_user;
DROP TABLE IF EXISTS push_notification_tokens CASCADE;

-- Drop indexes and tables for remembered_partners
DROP INDEX IF EXISTS idx_remembered_partners_last_played;
DROP INDEX IF EXISTS idx_remembered_partners_partner;
DROP INDEX IF EXISTS idx_remembered_partners_user;
DROP TABLE IF EXISTS remembered_partners CASCADE;

-- Drop indexes and tables for partner_connections
DROP INDEX IF EXISTS idx_partner_connections_expires;
DROP INDEX IF EXISTS idx_partner_connections_token;
DROP INDEX IF EXISTS idx_partner_connections_status;
DROP INDEX IF EXISTS idx_partner_connections_recipient_user;
DROP INDEX IF EXISTS idx_partner_connections_recipient_email;
DROP INDEX IF EXISTS idx_partner_connections_requester;
DROP TABLE IF EXISTS partner_connections CASCADE;

-- Drop enums
DROP TYPE IF EXISTS platform_enum CASCADE;
DROP TYPE IF EXISTS connection_status_enum CASCADE;

-- Rollback complete

