-- Add recipient_display_name column to partner_connections
ALTER TABLE partner_connections 
ADD COLUMN IF NOT EXISTS recipient_display_name TEXT;

-- Backfill existing records
-- Priority 1: Match by recipient_user_id
UPDATE partner_connections pc
SET recipient_display_name = u.display_name
FROM users u
WHERE pc.recipient_user_id = u.id
AND pc.recipient_display_name IS NULL;

-- Priority 2: Match by recipient_email (for pending connections where user exists but ID might not be linked yet)
UPDATE partner_connections pc
SET recipient_display_name = u.display_name
FROM users u
WHERE pc.recipient_email = u.email
AND pc.recipient_display_name IS NULL;

-- Trigger 1: Auto-populate on INSERT to partner_connections
CREATE OR REPLACE FUNCTION populate_recipient_name()
RETURNS TRIGGER AS $$
BEGIN
    -- Only populate if not already provided
    IF NEW.recipient_display_name IS NULL THEN
        -- Try to find by ID first
        IF NEW.recipient_user_id IS NOT NULL THEN
            SELECT display_name INTO NEW.recipient_display_name
            FROM users
            WHERE id = NEW.recipient_user_id;
        END IF;
        
        -- If still null, try by email
        IF NEW.recipient_display_name IS NULL THEN
            SELECT display_name INTO NEW.recipient_display_name
            FROM users
            WHERE email = NEW.recipient_email;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_populate_recipient_name ON partner_connections;
CREATE TRIGGER trigger_populate_recipient_name
BEFORE INSERT ON partner_connections
FOR EACH ROW
EXECUTE FUNCTION populate_recipient_name();

-- Trigger 2: Sync updates from users table to partner_connections (Recipient)
CREATE OR REPLACE FUNCTION sync_recipient_name_to_connections()
RETURNS TRIGGER AS $$
BEGIN
    -- If display_name changed, update all connection records where this user is the recipient
    IF OLD.display_name IS DISTINCT FROM NEW.display_name THEN
        UPDATE partner_connections
        SET recipient_display_name = NEW.display_name
        WHERE recipient_user_id = NEW.id;
        
        -- Also update by email just in case ID is not set (though unlikely for existing users)
        UPDATE partner_connections
        SET recipient_display_name = NEW.display_name
        WHERE recipient_email = NEW.email
        AND recipient_user_id IS NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: We can attach multiple triggers to the same event. 
-- We already have 'trigger_sync_user_name_to_connections' for requester.
-- Let's create a new one for recipient to keep logic separate and clean.

DROP TRIGGER IF EXISTS trigger_sync_recipient_name_to_connections ON users;
CREATE TRIGGER trigger_sync_recipient_name_to_connections
AFTER UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION sync_recipient_name_to_connections();
