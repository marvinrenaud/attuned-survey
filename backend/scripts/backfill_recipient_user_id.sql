-- Backfill recipient_user_id in partner_connections
-- Matches recipient_email to users.email and populates the ID if the user exists

UPDATE partner_connections pc
SET recipient_user_id = u.id
FROM users u
WHERE pc.recipient_email = u.email
AND pc.recipient_user_id IS NULL;
