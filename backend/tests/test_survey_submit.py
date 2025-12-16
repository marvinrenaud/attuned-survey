import pytest
from unittest.mock import patch
import uuid
from datetime import datetime
from backend.src.models.user import User
from backend.src.models.survey import SurveyProgress, SurveySubmission
from backend.src.models.profile import Profile
from backend.src.extensions import db
import backend.src.routes.survey_submit # Explicit import to fix patch resolution

@pytest.fixture
def auth_header():
    return {'Authorization': 'Bearer test-token'}

@pytest.fixture
def survey_data():
    return {
        'survey_version': '0.4',
        'answers': {
            'A1': 5,
            'B1': 6,
            'C1': ['hard_limit'],
            'D1': ['penis'],
            'D2': ['vagina']
        }
    }

@patch('backend.src.routes.survey_submit.get_current_user_id')
@patch('backend.src.routes.survey_submit.calculate_profile')
def test_submit_survey_success(mock_calc, mock_get_user, client, db_session, auth_header, survey_data):
    """Test successful atomic survey submission."""
    # Setup
    user_id = uuid.uuid4()
    mock_get_user.return_value = user_id
    
    # Mock profile calculation result
    mock_calc.return_value = {
        'profile_version': '0.4',
        'power_dynamic': {'orientation': 'Switch'},
        'arousal_propensity': {'se': 0.5},
        'domain_scores': {'sensation': 50},
        'activities': {'act1': 1.0},
        'truth_topics': {'topic1': 0.5},
        'boundaries': {'hard_limits': ['limit1']},
        'anatomy': {'anatomy_self': ['penis'], 'anatomy_preference': ['vagina']},
        'activity_tags': {}
    }

    # Create User
    user = User(id=user_id, email='test@example.com', onboarding_completed=False)
    db_session.add(user)
    
    # Create Progress
    progress = SurveyProgress(
        user_id=user_id,
        survey_version='0.4',
        status='in_progress',
        answers={}
    )
    db_session.add(progress)
    db_session.commit()

    # Execute
    response = client.post(
        '/api/survey/submit',
        json=survey_data,
        headers=auth_header
    )

    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert 'profile_id' in data
    
    # Verify DB State
    # 1. Submission created
    submission = SurveySubmission.query.filter_by(user_id=user_id).first()
    assert submission is not None
    assert submission.survey_progress_id == progress.id
    
    # 2. Profile created
    profile = Profile.query.filter_by(user_id=user_id).first()
    assert profile is not None
    assert profile.submission_id == submission.submission_id
    
    # 3. Progress updated
    updated_progress = SurveyProgress.query.get(progress.id)
    assert updated_progress.status == 'completed'
    assert updated_progress.completed_at is not None
    
    # 4. User updated
    updated_user = User.query.get(user_id)
    assert updated_user.onboarding_completed is True

@patch('backend.src.routes.survey_submit.get_current_user_id')
def test_submit_survey_idempotency(mock_get_user, client, db_session, auth_header, survey_data):
    """Test idempotency: second submission should return existing profile."""
    # Setup
    user_id = uuid.uuid4()
    mock_get_user.return_value = user_id
    
    # Create User
    user = User(id=user_id, email='test@example.com', onboarding_completed=True)
    db_session.add(user)
    
    # Create Completed Progress
    progress = SurveyProgress(
        user_id=user_id,
        survey_version='0.4',
        status='completed',
        completed_at=datetime.utcnow(),
        answers={}
    )
    db_session.add(progress)
    db_session.flush()
    
    # Create Existing Submission & Profile
    sub_id = str(uuid.uuid4())
    submission = SurveySubmission(
        submission_id=sub_id,
        user_id=user_id,
        survey_progress_id=progress.id,
        payload_json={}
    )
    db_session.add(submission)
    
    profile = Profile(
        user_id=user_id,
        submission_id=sub_id,
        power_dynamic={},
        arousal_propensity={},
        domain_scores={},
        activities={},
        truth_topics={},
        boundaries={},
        anatomy={}
    )
    db_session.add(profile)
    db_session.commit()

    # Execute
    response = client.post(
        '/api/survey/submit',
        json=survey_data,
        headers=auth_header
    )

    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert data['profile_id'] == profile.id
    assert data['message'] == 'Survey already completed'

@patch('backend.src.routes.survey_submit.get_current_user_id')
@patch('backend.src.routes.survey_submit.calculate_profile')
def test_submit_survey_rollback(mock_calc, mock_get_user, client, db_session, auth_header, survey_data):
    """Test transaction rollback on error."""
    # Setup
    user_id = uuid.uuid4()
    mock_get_user.return_value = user_id
    
    # Mock error during calculation
    mock_calc.side_effect = Exception("Calculation failed")

    # Create User & Progress
    user = User(id=user_id, email='test@example.com', onboarding_completed=False)
    db_session.add(user)
    progress = SurveyProgress(
        user_id=user_id,
        survey_version='0.4',
        status='in_progress'
    )
    db_session.add(progress)
    db_session.commit()

    # Execute
    response = client.post(
        '/api/survey/submit',
        json=survey_data,
        headers=auth_header
    )

    # Assert
    assert response.status_code == 500
    
    # Verify Rollback
    updated_progress = SurveyProgress.query.get(progress.id)
    assert updated_progress.status == 'in_progress'
    
    updated_user = User.query.get(user_id)
    assert updated_user.onboarding_completed is False
    
    assert SurveySubmission.query.filter_by(user_id=user_id).first() is None
    assert Profile.query.filter_by(user_id=user_id).first() is None

@patch('backend.src.routes.survey_submit.get_current_user_id')
def test_submit_survey_no_progress(mock_get_user, client, db_session, auth_header, survey_data):
    """Test 404 if no progress found."""
    user_id = uuid.uuid4()
    mock_get_user.return_value = user_id
    
    # Create User but NO Progress
    user = User(id=user_id, email='test@example.com')
    db_session.add(user)
    db_session.commit()

    response = client.post(
        '/api/survey/submit',
        json=survey_data,
        headers=auth_header
    )

    assert response.status_code == 404
