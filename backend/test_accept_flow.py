
import sys
import os
import json
from datetime import datetime, timedelta
import uuid

# Add the backend directory to the python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.main import create_app
from src.extensions import db
from src.routes.partners import PartnerConnection
from src.models.user import User

app = create_app()
app.config['TESTING'] = True
app.config['SQLALCHEMY_ECHO'] = False # Disable verbose SQL logs

def test_accept_flow():
    with app.test_client() as client:
        with app.app_context():
            print("Setting up test data...")
            # Create dummy users
            requester_id = uuid.uuid4()
            recipient_id = uuid.uuid4()
            requester = User(id=requester_id, email=f"req_{requester_id}@test.com", display_name="Requester")
            recipient = User(id=recipient_id, email=f"rec_{recipient_id}@test.com", display_name="Recipient")
            db.session.add(requester)
            db.session.add(recipient)
            db.session.commit()
            
            # Create connection
            conn = PartnerConnection(
                requester_user_id=requester.id,
                recipient_email=recipient.email,
                recipient_user_id=recipient.id, # Pre-populated
                status='pending',
                connection_token=str(uuid.uuid4()),
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            db.session.add(conn)
            db.session.commit()
            conn_id = conn.id
            recipient_id_str = str(recipient.id)
            print(f"Created connection ID: {conn_id}")

        # Test 1: Accept with valid recipient_user_id in body
        print("\nTest 1: Accept with valid recipient_user_id in body")
        res = client.post(f'/api/partners/connections/{conn_id}/accept', 
                          json={'recipient_user_id': recipient_id_str})
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")
        
        # Reset status
        with app.app_context():
            conn = PartnerConnection.query.get(conn_id)
            conn.status = 'pending'
            db.session.commit()

        # Test 2: Accept with NO body (empty)
        print("\nTest 2: Accept with NO body (empty)")
        res = client.post(f'/api/partners/connections/{conn_id}/accept')
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")
        
        # Test 3: Accept with empty JSON object {}
        print("\nTest 3: Accept with empty JSON object {}")
        res = client.post(f'/api/partners/connections/{conn_id}/accept', 
                          json={})
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")

        # Test 4: Accept with INVALID UUID in body
        print("\nTest 4: Accept with INVALID UUID in body")
        res = client.post(f'/api/partners/connections/{conn_id}/accept', 
                          json={'recipient_user_id': 'invalid-uuid'})
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")

        # Test 5: Accept with INVALID Connection ID (String instead of Int)
        print("\nTest 5: Accept with INVALID Connection ID (String)")
        res = client.post('/api/partners/connections/invalid-id/accept', 
                          json={})
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")

if __name__ == "__main__":
    test_accept_flow()
