
import sys
import os
import json
from datetime import datetime
import uuid

# Add the backend directory to the python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.main import create_app
from src.extensions import db
from src.routes.partners import RememberedPartner
from src.models.user import User

app = create_app()
app.config['TESTING'] = True
app.config['SQLALCHEMY_ECHO'] = False

def test_remembered_partners():
    with app.test_client() as client:
        with app.app_context():
            print("Setting up test data...")
            # Create dummy users
            u1_id = uuid.uuid4()
            u2_id = uuid.uuid4()
            u1 = User(id=u1_id, email=f"u1_{u1_id}@test.com", display_name="User 1")
            u2 = User(id=u2_id, email=f"u2_{u2_id}@test.com", display_name="User 2")
            db.session.add(u1)
            db.session.add(u2)
            db.session.commit()
            
            # Create remembered partner entry
            rp = RememberedPartner(
                user_id=u1_id,
                partner_user_id=u2_id,
                partner_name="User 2",
                partner_email=u2.email,
                last_played_at=datetime.utcnow()
            )
            db.session.add(rp)
            db.session.commit()
            rp_id = rp.id
            print(f"Created RememberedPartner ID: {rp_id}")
            
            u1_id_str = str(u1_id)
            u2_id_str = str(u2_id)

        # Test 1: GET remembered partners
        print(f"\nTest 1: GET /api/partners/remembered/{u1_id_str}")
        res = client.get(f'/api/partners/remembered/{u1_id_str}')
        print(f"Status: {res.status_code}")
        data = res.get_json()
        print(f"Response: {data}")
        
        if res.status_code == 200 and len(data.get('partners', [])) > 0:
            print("SUCCESS: Retrieved remembered partners")
            # Verify data types
            partner = data['partners'][0]
            if partner['partner_user_id'] == u2_id_str:
                print("SUCCESS: Partner ID matches")
            else:
                print(f"FAILURE: Partner ID mismatch. Expected {u2_id_str}, got {partner['partner_user_id']}")
        else:
            print("FAILURE: Could not retrieve partners")

        # Test 2: DELETE remembered partner
        print(f"\nTest 2: DELETE /api/partners/remembered/{u1_id_str}/{u2_id_str}")
        res = client.delete(f'/api/partners/remembered/{u1_id_str}/{u2_id_str}')
        print(f"Status: {res.status_code}")
        print(f"Response: {res.get_json()}")
        
        if res.status_code == 200:
            print("SUCCESS: Deleted remembered partner")
        else:
            print("FAILURE: Could not delete partner")

        # Verify deletion
        with app.app_context():
            exists = RememberedPartner.query.filter_by(id=rp_id).first()
            if not exists:
                print("SUCCESS: Record verified deleted from DB")
            else:
                print("FAILURE: Record still exists in DB")

if __name__ == "__main__":
    test_remembered_partners()
