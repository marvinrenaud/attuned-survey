import pytest
from unittest.mock import patch, MagicMock
from backend.src.models.survey import SurveySubmission
from backend.src.models.profile import Profile
from backend.src.models.user import User
from backend.src.extensions import db
import uuid

@pytest.fixture
def mobile_payload():
    return {
        "A1": 7,
        "A2": 7,
        "A3": 7,
        # ... minimal set for testing
    }

def test_process_mobile_submission(client, app, db_session, mobile_payload):
    """
    Test processing a submission that mimics the mobile app flow:
    - Flat payload (no 'answers' key)
    - user_id is set on the submission
    - Anatomy missing from payload
    """
    
    # 1. Setup: Create a User
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="mobile_test@example.com",
        display_name="Mobile Tester",
        has_penis=True,
        likes_vagina=True
    )
    db.session.add(user)
    db.session.commit()

    # 2. Setup: Create a Submission (Simulating FlutterFlow insert)
    submission_id = "mobile-sub-123"
    submission = SurveySubmission(
        submission_id=submission_id,
        user_id=user_id,
        payload_json=mobile_payload,
        version="0.4"
    )
    db.session.add(submission)
    db.session.commit()

    # 3. Action: Call the process endpoint
    # We mock calculate_profile to avoid complex scoring logic dependencies in this unit test
    # and focus on the flow (payload handling, user linking, anatomy sync)
    with patch('backend.src.routes.process_submission.calculate_profile') as mock_calc:
        mock_calc.return_value = {
            "profile_version": "0.4",
            "anatomy": {
                "anatomy_self": ["vagina"],
                "anatomy_preference": ["penis"]
            },
            "domain_scores": {"sensation": 50}
        }
        
        # We also want to verify sync_user_anatomy_to_profile is called
        with patch('backend.src.routes.process_submission.sync_user_anatomy_to_profile') as mock_sync:
            mock_sync.return_value = True
            
            response = client.post(f'/api/survey/submissions/{submission_id}/process')
            
            if response.status_code != 201:
                print(f"Error Response Data: {response.data}")
            assert response.status_code == 201
            
            # 4. Verification
            # Check Profile created
            profile = Profile.query.filter_by(submission_id=submission_id).first()
            assert profile is not None
            assert profile.user_id == user_id
            
            # Check Sync called
            mock_sync.assert_called_once_with(str(user_id))
            
            # Check Calculate called with correct args
            # It should pass the user_id and the flat payload as answers
            mock_calc.assert_called_once()
            args, _ = mock_calc.call_args
            assert args[0] == str(user_id)
            assert args[1] == mobile_payload

def test_process_web_submission(client, app, db_session):
    """
    Test processing a submission that mimics the web app flow:
    - Nested payload ('answers' key)
    - user_id might be None initially (or set)
    """
    submission_id = "web-sub-123"
    nested_payload = {
        "answers": {"A1": 5},
        "version": "0.4"
    }
    
    submission = SurveySubmission(
        submission_id=submission_id,
        payload_json=nested_payload
    )
    db.session.add(submission)
    db.session.commit()

    with patch('backend.src.routes.process_submission.calculate_profile') as mock_calc:
        mock_calc.return_value = {
            "profile_version": "0.4",
            "anatomy": {
                "anatomy_self": ["vagina"],
                "anatomy_preference": ["penis"]
            },
            "domain_scores": {"sensation": 50}
        }
        
        response = client.post(f'/api/survey/submissions/{submission_id}/process')
        
        assert response.status_code == 201
        
        # Verify it extracted 'answers' correctly
        mock_calc.assert_called_once()
        args, _ = mock_calc.call_args
        assert args[1] == nested_payload['answers']
