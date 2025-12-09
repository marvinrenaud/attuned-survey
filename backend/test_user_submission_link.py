
import sys
import os
import json
import uuid
from datetime import datetime

# Add the backend directory to the python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.main import create_app
from src.extensions import db
from src.models.user import User
from src.models.survey import SurveySubmission

app = create_app()
app.config['TESTING'] = True
app.config['SQLALCHEMY_ECHO'] = False

def test_user_submission_link():
    with app.test_client() as client:
        print("--- Test: Verify submission_id in User Profile ---")
        
        # 1. Create User
        u_id = str(uuid.uuid4())
        with app.app_context():
            user = User(id=u_id, email=f"link_test_{u_id}@test.com", display_name="Link Test User")
            db.session.add(user)
            db.session.commit()
            
        # 2. Check Profile (Should have None submission_id)
        print("Checking profile before submission...")
        res = client.get(f'/api/auth/user/{u_id}')
        assert res.status_code == 200
        data = res.get_json()
        if data['user']['submission_id'] is None:
            print("SUCCESS: submission_id is None as expected")
        else:
            print(f"FAILURE: Expected None, got {data['user']['submission_id']}")
            return

        # 3. Create Submission linked to User
        sub_id = f"sub_{u_id}"
        with app.app_context():
            # We manually create it to ensure the link is established as per our model changes
            # The API would do this via the logic we added earlier, but here we test the model link directly
            submission = SurveySubmission(
                submission_id=sub_id,
                user_id=u_id,
                payload_json={},
                created_at=datetime.utcnow()
            )
            db.session.add(submission)
            db.session.commit()
            
        # 4. Check Profile (Should have submission_id)
        print("Checking profile after submission...")
        res = client.get(f'/api/auth/user/{u_id}')
        assert res.status_code == 200
        data = res.get_json()
        
        actual_sub_id = data['user']['submission_id']
        print(f"Expected: {sub_id}")
        print(f"Actual:   {actual_sub_id}")
        
        if actual_sub_id == sub_id:
            print("SUCCESS: submission_id matches")
        else:
            print("FAILURE: submission_id mismatch")

if __name__ == "__main__":
    test_user_submission_link()
