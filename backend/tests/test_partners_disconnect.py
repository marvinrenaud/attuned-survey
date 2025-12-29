import pytest
import uuid
import json
from datetime import datetime, timedelta
from backend.src.models.user import User

# Helper to create a user and force commit
def create_user(db_session, email):
    user = User(
        id=uuid.uuid4(),
        email=email,
        display_name=f"User {email}",
        auth_provider='email'
    )
    db_session.add(user)
    db_session.commit()
    return user

def test_partner_disconnect_lifecycle(client, db_session, app):
    """
    Test the full lifecycle:
    1. Connect (Pending)
    2. Accept (Accepted)
    3. Verify Memory
    4. Disconnect (Removed/Disconnected)
    5. Verify Clean Slate (Reciprocal delete)
    6. Re-connect (New active connection)
    """
    
    # 1. Setup Users
    user_a = create_user(db_session, "a@test.com")
    user_b = create_user(db_session, "b@test.com")
    
    # Needs profiles for compatibility calc (even if empty, just to avoid errors if triggered)
    # The accept_connection route handles missing profiles gracefully (logs warning), so skipping profile creation for speed.
    
    # 2. A requests B
    resp = client.post('/api/partners/connect', json={
        'requester_user_id': str(user_a.id),
        'recipient_email': user_b.email
    })
    assert resp.status_code == 201
    conn_data = resp.get_json()['connection']
    conn_id_1 = conn_data['id']
    assert conn_data['status'] == 'pending'
    
    # 3. B accepts A
    resp = client.post(f'/api/partners/connections/{conn_id_1}/accept', json={
        'recipient_user_id': user_b.id
    })
    assert resp.status_code == 200
    assert resp.get_json()['connection']['status'] == 'accepted'
    
    # 4. Verify Remembered Partners
    # Check A remembers B
    resp_a = client.get(f'/api/partners/remembered/{user_a.id}')
    assert resp_a.status_code == 200
    partners_a = resp_a.get_json()['partners']
    assert len(partners_a) == 1
    assert partners_a[0]['partner_email'] == user_b.email
    
    # Check B remembers A
    resp_b = client.get(f'/api/partners/remembered/{user_b.id}')
    assert resp_b.status_code == 200
    partners_b = resp_b.get_json()['partners']
    assert len(partners_b) == 1
    assert partners_b[0]['partner_email'] == user_a.email
    
    # Check Active Connection Logic (Should fail duplicates)
    # A tries to request B again
    resp_dup = client.post('/api/partners/connect', json={
        'requester_user_id': str(user_a.id),
        'recipient_email': user_b.email
    })
    assert resp_dup.status_code == 400
    assert "already connected" in resp_dup.get_json()['error']
    
    # 5. A Disconnects from B
    resp_del = client.delete(f'/api/partners/remembered/{user_a.id}/{user_b.id}')
    assert resp_del.status_code == 200
    
    # 6. Verify Disconnection Results
    
    # A's list empty
    resp_a_new = client.get(f'/api/partners/remembered/{user_a.id}')
    assert len(resp_a_new.get_json()['partners']) == 0
    
    # B's list empty (Reciprocal Delete!)
    resp_b_new = client.get(f'/api/partners/remembered/{user_b.id}')
    assert len(resp_b_new.get_json()['partners']) == 0
    
    # Connection status is 'disconnected'
    # Use direct DB check or get_connections endpoint
    # UPDATE: Endpoint filters out disconnected, so verify it's NOT in the list
    resp_conns = client.get(f'/api/partners/connections/{user_a.id}')
    conns = resp_conns.get_json()['connections']
    
    # Should NOT see the disconnected one
    target_conn = next((c for c in conns if c['id'] == conn_id_1), None)
    assert target_conn is None
    
    # Verify via DB that it is indeed disconnected
    from backend.src.routes.partners import PartnerConnection
    db_conn = PartnerConnection.query.get(conn_id_1)
    assert db_conn.status == 'disconnected'
    
    # 7. Re-connection
    # A requests B again
    resp_new = client.post('/api/partners/connect', json={
        'requester_user_id': str(user_a.id),
        'recipient_email': user_b.email
    })
    assert resp_new.status_code == 201
    new_conn_data = resp_new.get_json()['connection']
    conn_id_2 = new_conn_data['id']
    
    # Should be a NEW connection ID
    assert conn_id_2 != conn_id_1
    assert new_conn_data['status'] == 'pending'
    
    # 8. B Accepts New Connection
    resp_accept_new = client.post(f'/api/partners/connections/{conn_id_2}/accept', json={
        'recipient_user_id': user_b.id
    })
    assert resp_accept_new.status_code == 200
    
    # Verify both remembered again
    resp_a_final = client.get(f'/api/partners/remembered/{user_a.id}')
    assert len(resp_a_final.get_json()['partners']) == 1

def test_pending_request_validation(client, db_session, app):
    """Test validation prevents duplicate pending requests."""
    user_a = create_user(db_session, "a2@test.com")
    user_b = create_user(db_session, "b2@test.com")
    
    # A requests B
    client.post('/api/partners/connect', json={
        'requester_user_id': str(user_a.id),
        'recipient_email': user_b.email
    })
    
    # 1. A tries to request B again -> "Request already sent"
    resp_dup = client.post('/api/partners/connect', json={
        'requester_user_id': str(user_a.id),
        'recipient_email': user_b.email
    })
    assert resp_dup.status_code == 400
    assert "already sent" in resp_dup.get_json()['error']
    
    # 2. B tries to request A (Reverse direction check) -> "You have a pending request"
    # Note: B sends to A's email
    resp_rev = client.post('/api/partners/connect', json={
        'requester_user_id': str(user_b.id),
        'recipient_email': user_a.email
    })
    assert resp_rev.status_code == 400
    # The logic approximates this by checking if A received a request from B?
    # Wait, the logic in partners.py checks existing connections:
    # "Case 2: They sent request to me... (PartnerConnection.recipient_user_id == requester_id) & (PartnerConnection.recipient_email == requester.email)"
    
    # Logic trace:
    # Current requester = user_b.id
    # Current recipient_email = user_a.email
    # Query looks for:
    # (Requester=B & RecipientEmail=A) -> True if B sent before? No.
    # OR
    # (RecipientUser=B & RecipientEmail=B's Email) -> Checks if *I* (B) am recipient of something from A?
    # Wait, the approximation logic in partners.py:
    # `(PartnerConnection.recipient_user_id == requester_id) & (PartnerConnection.recipient_email == requester.email)`
    # In my test step 2: 
    # requester_id = B.
    # recipient_email = A.
    # The query `(PartnerConnection.recipient_user_id == requester_id)` relies on `recipient_user_id` being populated.
    # BUT for pending requests sending to *email*, `recipient_user_id` is typically NULL until they accept!
    # Let's check `create_connection_request` implementation:
    # `recipient_id = recipient.id if recipient else None`
    # So if the user EXISTS, `recipient_user_id` IS populated on create.
    # `create_user` in helpers creates the user.
    # So `recipient_user_id` should be set.
    
    assert "pending request" in resp_rev.get_json()['error']
