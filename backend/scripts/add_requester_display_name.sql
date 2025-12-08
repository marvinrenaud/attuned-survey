-- Add requester_display_name column to partner_connections
ALTER TABLE partner_connections 
ADD COLUMN IF NOT EXISTS requester_display_name TEXT;

-- Backfill existing records
UPDATE partner_connections pc
SET requester_display_name = u.display_name
FROM users u
WHERE pc.requester_user_id = u.id
AND pc.requester_display_name IS NULL;

-- Trigger 1: Auto-populate on INSERT to partner_connections
CREATE OR REPLACE FUNCTION populate_requester_name()
RETURNS TRIGGER AS $$
BEGIN
    -- Only populate if not already provided
    IF NEW.requester_display_name IS NULL THEN
        SELECT display_name INTO NEW.requester_display_name
        FROM users
        WHERE id = NEW.requester_user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_populate_requester_name ON partner_connections;
CREATE TRIGGER trigger_populate_requester_name
BEFORE INSERT ON partner_connections
FOR EACH ROW
EXECUTE FUNCTION populate_requester_name();

-- Trigger 2: Sync updates from users table to partner_connections
CREATE OR REPLACE FUNCTION sync_user_name_to_connections()
RETURNS TRIGGER AS $$
BEGIN
    -- If display_name changed, update all connection records where this user is the requester
    IF OLD.display_name IS DISTINCT FROM NEW.display_name THEN
        UPDATE partner_connections
        SET requester_display_name = NEW.display_name
        WHERE requester_user_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_sync_user_name_to_connections ON users;
CREATE TRIGGER trigger_sync_user_name_to_connections
AFTER UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION sync_user_name_to_connections();
