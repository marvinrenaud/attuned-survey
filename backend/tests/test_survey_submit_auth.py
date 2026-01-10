
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.routes.survey_submit import survey_submit_bp
from src.models.survey import SurveySubmission, SurveyProgress
from src.models.profile import Profile
from src.models.user import User
from src.extensions import db
import jwt
import os
import uuid
from datetime import datetime

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    app.register_blueprint(survey_submit_bp)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_calculate_profile():
    with patch('src.routes.survey_submit.calculate_profile') as mock_calc:
        # Return dummy profile data
        mock_calc.return_value = {
            'profile_version': '0.5',
            'anatomy': {'anatomy_self': [], 'anatomy_preference': []},
            'power_dynamic': {},
            'arousal_propensity': {},
            'domain_scores': {},
            'activities': {},
            'truth_topics': {},
            'boundaries': {},
            'activity_tags': {}
        }
        yield mock_calc

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_submit_survey_unauthorized(client):
    response = client.post('/api/survey/submit', json={})
    assert response.status_code == 401

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_submit_survey_success_new_profile(client, app, mock_calculate_profile):
    user_id_str = str(uuid.uuid4())
    user_id = uuid.UUID(user_id_str)
    token = jwt.encode({"sub": user_id_str, "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
    
    with app.app_context():
        # Setup: User, Progress (In Progress)
        user = User(id=user_id, email="test@example.com")
        db.session.add(user)
        
        progress = SurveyProgress(
            user_id=user_id,
            survey_version='0.4',
            status='in_progress',
            started_at=datetime.utcnow()
        )
        db.session.add(progress)
        db.session.commit()
    
    payload = {
        'answers': {'q1': 'a1'}
    }
    
    response = client.post('/api/survey/submit', 
                           json=payload,
                           headers={'Authorization': f'Bearer {token}'})
    
    
    assert response.status_code == 200, f"Error: {response.data.decode('utf-8')}"
    assert response.json['message'] == 'Survey submitted successfully'
    
    # Verify DB
    with app.app_context():
        p = Profile.query.filter_by(user_id=user_id).first()
        assert p is not None
        assert p.submission_id is not None
        
        sub = SurveySubmission.query.filter_by(submission_id=p.submission_id).first()
        assert sub is not None
        
        prg = SurveyProgress.query.filter_by(user_id=user_id).first()
        assert prg.status == 'completed'

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_submit_survey_upsert_retake(client, app, mock_calculate_profile):
    user_id_str = str(uuid.uuid4())
    user_id = uuid.UUID(user_id_str)
    token = jwt.encode({"sub": user_id_str, "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
    
    with app.app_context():
        # Setup: User, Completed Progress, Existing Profile
        user = User(id=user_id, email="retake@example.com", onboarding_completed=True)
        db.session.add(user)
        
        progress = SurveyProgress(
            user_id=user_id,
            survey_version='0.4',
            status='completed',
            started_at=datetime.utcnow()
        )
        db.session.add(progress)
        db.session.flush()
        
        # Existing submission/profile
        old_sub_id = str(uuid.uuid4())
        sub = SurveySubmission(
            submission_id=old_sub_id, 
            survey_progress_id=progress.id, 
            user_id=user_id,
            payload_json={}
        )
        db.session.add(sub)
        
        profile = Profile(
            user_id=user_id,
            submission_id=old_sub_id,
            profile_version='0.4',
            power_dynamic={},
            arousal_propensity={},
            domain_scores={},
            activities={},
            truth_topics={},
            boundaries={},
            activity_tags={},
            anatomy={}
        )
        db.session.add(profile)
        db.session.commit()
        
        old_profile_id = profile.id

    # Retake Request
    payload = {
        'answers': {'q1': 'new_answer'},
        'retake': True
    }
    
    response = client.post('/api/survey/submit', 
                           json=payload,
                           headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    
    with app.app_context():
        # Check Profile Updated (Same ID, new submission_id)
        p = Profile.query.filter_by(user_id=user_id).first()
        assert p.id == old_profile_id  # Should be same row (Upserted)
        assert p.submission_id != old_sub_id # Should point to new submission
        
        # Check New Submission Exists
        new_sub = SurveySubmission.query.filter_by(submission_id=p.submission_id).first()
        assert new_sub is not None
        assert new_sub.payload_json == {'q1': 'new_answer'}
