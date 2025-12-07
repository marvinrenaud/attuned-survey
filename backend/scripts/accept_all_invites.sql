DO $$
DECLARE
    r RECORD;
    v_requester_name TEXT;
    v_recipient_name TEXT;
    v_requester_email TEXT;
BEGIN
    -- Loop through all pending connections where the recipient email exists in the users table
    FOR r IN 
        SELECT pc.id, pc.requester_user_id, pc.recipient_email, u.id AS recipient_user_id
        FROM partner_connections pc
        JOIN users u ON u.email = pc.recipient_email
        WHERE pc.status = 'pending'
    LOOP
        -- 1. Update partner_connections
        UPDATE partner_connections
        SET status = 'accepted',
            recipient_user_id = r.recipient_user_id,
            updated_at = NOW()
        WHERE id = r.id;

        -- Get requester details
        SELECT COALESCE(display_name, 'Partner'), email 
        INTO v_requester_name, v_requester_email 
        FROM users 
        WHERE id = r.requester_user_id;

        -- Get recipient details
        SELECT COALESCE(display_name, 'Partner') 
        INTO v_recipient_name 
        FROM users 
        WHERE id = r.recipient_user_id;

        -- 2. Insert into remembered_partners (Requester remembers Recipient)
        INSERT INTO remembered_partners (user_id, partner_user_id, partner_name, partner_email, last_played_at)
        VALUES (r.requester_user_id, r.recipient_user_id, v_recipient_name, r.recipient_email, NOW())
        ON CONFLICT (user_id, partner_user_id) DO UPDATE 
        SET last_played_at = NOW();

        -- 3. Insert into remembered_partners (Recipient remembers Requester)
        INSERT INTO remembered_partners (user_id, partner_user_id, partner_name, partner_email, last_played_at)
        VALUES (r.recipient_user_id, r.requester_user_id, v_requester_name, v_requester_email, NOW())
        ON CONFLICT (user_id, partner_user_id) DO UPDATE 
        SET last_played_at = NOW();
        
        RAISE NOTICE 'Accepted connection % between % and %', r.id, r.requester_user_id, r.recipient_user_id;
    END LOOP;
END $$;
