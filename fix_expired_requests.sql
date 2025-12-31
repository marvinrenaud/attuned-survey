-- Reactivate partner requests created in the last 24 hours that expired too quickly
-- This applies the new 1-day expiration rule retroactively

UPDATE partner_connections
SET 
    status = 'pending',
    expires_at = created_at + INTERVAL '1 day'
WHERE 
    status = 'expired' 
    AND created_at > (NOW() - INTERVAL '1 day')
    -- Optional: target specific token if needed, but the above covers all recent ones
    -- AND connection_token = '06679c23-c3ed-4225-ab84-bcba675e8020' 
;

-- Verify the update
SELECT id, requester_user_id, recipient_email, status, created_at, expires_at
FROM partner_connections
WHERE created_at > (NOW() - INTERVAL '1 day')
ORDER BY created_at DESC;
