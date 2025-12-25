import pytest
import uuid
from datetime import datetime
from backend.src.models.user import User
from backend.src.models.survey import SurveySubmission, SurveyProgress
from backend.src.models.profile import Profile
from backend.src.extensions import db

@pytest.fixture
def user_with_progress(client, db_session):
    """Create a user and their initial survey progress."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"test_retake_{user_id}@example.com",
        onboarding_completed=False
    )
    db_session.add(user)
    
    # Create progress
    progress = SurveyProgress(
        user_id=user_id,
        survey_version='0.4',
        status='in_progress',
        answers={},
        completion_percentage=0,
        started_at=datetime.utcnow()
    )
    db_session.add(progress)
    db_session.commit()
    
    return user

def test_survey_retake_flow(client, user_with_progress, db_session):
    """
    Test the full lifecycle:
    1. Submit Survey (Complete)
    2. Submit Again (Block)
    3. Retake (Allow & New Profile)
    """
    user_id = user_with_progress.id
    
    # Mock authentication by patching get_current_user_id logic 
    # OR simpler: use the existing test pattern of passing user_id if supported, 
    # but the route calls get_current_user_id(). 
    # We'll need to mock that or rely on a testing override.
    # Assuming conftest.py handles auth mocking or we simulate a token.
    # For now, let's assume we can mock the auth dependency or the test client is configured.
    # Wait, the route uses `get_current_user_id()`. We need to mock it.
    
    # Mock authentication by patching get_current_user_id logic 
    # We patch the import in the route module
    from unittest.mock import patch
    
    answers_v1 = {"q1": 1, "sexual_excitation": 5}
    answers_v2 = {"q1": 2, "sexual_excitation": 8} # Different answers
    
    
    mock_profile_data = {
        'power_dynamic': {'orientation': 'Switch', 'confidence': 75},
        'arousal_propensity': {'se': 0.7, 'sis_p': 0.3, 'sis_c': 0.5},
        'domain_scores': {
            'sensation': 65,
            'connection': 70,
            'power': 60,
            'exploration': 55,
            'verbal': 75
        },
        'activities': {},
        'boundaries': {'hard_limits': []},
        'anatomy': {}
    }

    with patch('backend.src.routes.survey_submit.get_current_user_id', return_value=user_id), \
         patch('backend.src.routes.survey_submit.calculate_profile', return_value=mock_profile_data):
        
        # 1. INITIAL SUBMISSION
        resp = client.post('/api/survey/submit', json={
            "survey_version": "0.4",
            "answers": answers_v1
        })
        if resp.status_code != 200:
            print(f"Error Response: {resp.get_json()}")
        assert resp.status_code == 200
        data = resp.get_json()
        profile_id_v1 = data['profile_id']
        
        # Verify DB state
        progress = SurveyProgress.query.filter_by(user_id=user_id).first()
        assert progress.status == 'completed'
        
        # 2. DUPLICATE ATTEMPT (Without retake flag)
        resp = client.post('/api/survey/submit', json={
            "survey_version": "0.4",
            "answers": answers_v2
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['message'] == 'Survey already completed'
        # Profile ID should be the OLD one
        assert data.get('profile_id') == profile_id_v1 or data.get('profile_id') is None
        
        # Verify no new profile created
        assert Profile.query.filter_by(user_id=user_id).count() == 1
        
        # 3. RETAKE ATTEMPT (With retake flag)
        resp = client.post('/api/survey/submit', json={
            "survey_version": "0.4",
            "answers": answers_v2,
            "retake": True
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['message'] == 'Survey submitted successfully'
        profile_id_v2 = data['profile_id']
        
        # Verify IDs are different
        assert profile_id_v1 != profile_id_v2
        
        # 4. VERIFY DB STATE
        # A. Profile Count
        profiles = Profile.query.filter_by(user_id=user_id).order_by(Profile.created_at.asc()).all()
        assert len(profiles) == 2
        
        # B. Profile Linkage (Profile V2 -> Submission V2)
        profile_v2 = profiles[1]
        submission_v2 = SurveySubmission.query.filter_by(submission_id=profile_v2.submission_id).first()
        assert submission_v2 is not None
        assert submission_v2.payload_json == answers_v2 # Should have NEW answers
        
        # C. Progress Sync
        db_session.refresh(progress)
        assert progress.status == 'completed'
        assert progress.answers == answers_v2 # Should reflect LATEST answers
        
        # D. User UI Discoverability Check (Direct DB)
        # Verify that the query used by profile_ui returns the NEW profile
        latest_profile = Profile.query.filter_by(user_id=user_id).order_by(Profile.created_at.desc()).first()
        assert latest_profile.id == profile_v2.id
        
        # Verify mocked data persistence
        # Note: SQLAlchemy/SQLite JSON handling might return dicts or objects depending on driver, 
        # but since we patched calculate_profile, these columns should contain the mock data.
        assert latest_profile.power_dynamic == mock_profile_data['power_dynamic']
        assert latest_profile.arousal_propensity == mock_profile_data['arousal_propensity']
