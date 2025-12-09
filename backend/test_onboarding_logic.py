
import sys
import os
import json
import uuid

# Add the backend directory to the python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.main import create_app
from src.extensions import db
from src.models.user import User
from src.models.survey import SurveySubmission

app = create_app()
app.config['TESTING'] = True
app.config['SQLALCHEMY_ECHO'] = False

def test_onboarding_logic():
    with app.test_client() as client:
        print("--- Test 1: Profile First, Then Survey ---")
        u1_id = str(uuid.uuid4())
        with app.app_context():
            u1 = User(id=u1_id, email=f"u1_{u1_id}@test.com", display_name="User 1")
            db.session.add(u1)
            db.session.commit()
            
        # 1. Complete Demographics
        print("Completing demographics...")
        res = client.post(f'/api/auth/user/{u1_id}/complete-demographics', json={
            'name': 'User One',
            'has_penis': True,
            'likes_vagina': True
        })
        assert res.status_code == 200
        
        # Check status (Should be False, no survey yet)
        with app.app_context():
            u1 = User.query.get(u1_id)
            print(f"Onboarding Completed (Expect False): {u1.onboarding_completed}")
            if u1.onboarding_completed:
                print("FAILURE: Onboarding marked complete too early")
                return

        # 2. Submit Survey
        print("Submitting survey...")
        res = client.post('/api/survey/submissions', json={
            'respondent_id': u1_id, # This links to user
            'answers': {'q1': 1}
        })
        assert res.status_code == 201
        
        # Check status (Should be True)
        with app.app_context():
            u1 = User.query.get(u1_id)
            print(f"Onboarding Completed (Expect True): {u1.onboarding_completed}")
            if not u1.onboarding_completed:
                print("FAILURE: Onboarding NOT marked complete after survey")
                return
            else:
                print("SUCCESS: Test 1 Passed")

        print("\n--- Test 2: Survey First, Then Profile ---")
        u2_id = str(uuid.uuid4())
        with app.app_context():
            u2 = User(id=u2_id, email=f"u2_{u2_id}@test.com", display_name="User 2")
            db.session.add(u2)
            db.session.commit()
            
        # 1. Submit Survey
        print("Submitting survey...")
        res = client.post('/api/survey/submissions', json={
            'respondent_id': u2_id,
            'answers': {'q1': 1}
        })
        assert res.status_code == 201
        
        # Check status (Should be False, no profile yet)
        with app.app_context():
            u2 = User.query.get(u2_id)
            print(f"Onboarding Completed (Expect False): {u2.onboarding_completed}")
            if u2.onboarding_completed:
                print("FAILURE: Onboarding marked complete too early")
                return

        # 2. Complete Demographics
        print("Completing demographics...")
        res = client.post(f'/api/auth/user/{u2_id}/complete-demographics', json={
            'name': 'User Two',
            'has_vagina': True,
            'likes_penis': True
        })
        assert res.status_code == 200
        
        # Check status (Should be True)
        with app.app_context():
            u2 = User.query.get(u2_id)
            print(f"Onboarding Completed (Expect True): {u2.onboarding_completed}")
            if not u2.onboarding_completed:
                print("FAILURE: Onboarding NOT marked complete after demographics")
                return
            else:
                print("SUCCESS: Test 2 Passed")

if __name__ == "__main__":
    test_onboarding_logic()
