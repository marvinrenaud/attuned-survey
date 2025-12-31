
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.routes.compatibility import compatibility_bp
from src.models.user import User
from src.models.profile import Profile
from src.models.compatibility import Compatibility
from src.models.survey import SurveySubmission
from src.routes.partners import PartnerConnection
from src.extensions import db
import jwt
import os
import uuid
from datetime import datetime
import logging

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    app.register_blueprint(compatibility_bp)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def create_full_profile(id, user_id, submission_id):
    return Profile(
        id=id, 
        user_id=user_id, 
        submission_id=submission_id,
        profile_version='0.4',
        power_dynamic={'orientation': 'Switch', 'top_score': 5, 'bottom_score': 5},
        arousal_propensity={},
        domain_scores={'sensation': 5, 'connection': 5},
        activities={'sensual': {'massage': 10}},
        truth_topics={},
        boundaries={'hard_limits': []},
        activity_tags={},
        anatomy={}
    )

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_compat_unauthorized(client):
    response = client.get('/api/compatibility/uid1/uid2')
    assert response.status_code == 401

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_compat_forbidden(client, app):
    # User 3 tries to view 1-2
    u1_id = str(uuid.uuid4())
    u2_id = str(uuid.uuid4())
    u3_id = str(uuid.uuid4())
    token3 = jwt.encode({"sub": u3_id, "aud": "authenticated"}, "test_secret", algorithm="HS256")
    
    response = client.get(f'/api/compatibility/{u1_id}/{u2_id}', headers={'Authorization': f'Bearer {token3}'})
    assert response.status_code == 403

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_compat_success(client, app):
    u1_id = str(uuid.uuid4())
    u2_id = str(uuid.uuid4())
    token1 = jwt.encode({"sub": u1_id, "aud": "authenticated"}, "test_secret", algorithm="HS256")
    
    try:
        with app.app_context():
            u1 = User(id=uuid.UUID(u1_id), email="u1@e.com", display_name="U1")
            u2 = User(id=uuid.UUID(u2_id), email="u2@e.com", display_name="U2", profile_sharing_setting="all_responses")
            db.session.add_all([u1, u2])
            db.session.commit()
            
            # Partner Connection
            conn = PartnerConnection(
                requester_user_id=u1_id, 
                recipient_user_id=u2_id, 
                status='accepted', 
                recipient_email="u2@e.com",
                connection_token="token123",
                expires_at=datetime.utcnow()
            )
            db.session.add(conn)
            db.session.commit()
            
            # Submissions
            s1 = SurveySubmission(submission_id="sub1", payload_json={})
            s2 = SurveySubmission(submission_id="sub2", payload_json={})
            db.session.add_all([s1, s2])
            db.session.commit()
            
            # Profiles
            p1 = create_full_profile(1, uuid.UUID(u1_id), "sub1")
            p2 = create_full_profile(2, uuid.UUID(u2_id), "sub2")
            db.session.add_all([p1, p2])
            db.session.commit()
            
            # Compatibility
            comp = Compatibility(
                player_a_id=1, 
                player_b_id=2, 
                overall_score=0.85,
                overall_percentage=85, 
                interpretation="Good",
                breakdown={'power': 10},
                id=1
            )
            db.session.add(comp)
            db.session.commit()
            
        response = client.get(f'/api/compatibility/{u1_id}/{u2_id}', headers={'Authorization': f'Bearer {token1}'})
        assert response.status_code == 200
        assert response.json['overall_compatibility']['score'] == 85
    except Exception as e:
        print(f"DEBUG EXCEPTION: {e}")
        raise e

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_compat_ui_success(client, app):
    u1_id = str(uuid.uuid4())
    u2_id = str(uuid.uuid4())
    token1 = jwt.encode({"sub": u1_id, "aud": "authenticated"}, "test_secret", algorithm="HS256")
    
    try:
        with app.app_context():
            u1 = User(id=uuid.UUID(u1_id), email="u1@e.com", display_name="U1")
            u2 = User(id=uuid.UUID(u2_id), email="u2@e.com", display_name="U2", profile_sharing_setting="all_responses")
            db.session.add_all([u1, u2])
            db.session.commit()
            
            s1 = SurveySubmission(submission_id="sub1", payload_json={})
            s2 = SurveySubmission(submission_id="sub2", payload_json={})
            db.session.add_all([s1, s2])
            db.session.commit()
            
            p1 = create_full_profile(1, uuid.UUID(u1_id), "sub1")
            p2 = create_full_profile(2, uuid.UUID(u2_id), "sub2")
            db.session.add_all([p1, p2])
            db.session.commit()
            
            comp = Compatibility(player_a_id=1, player_b_id=2, overall_score=0.9, overall_percentage=90, interpretation="Great", breakdown={'power': 10}, id=1)
            db.session.add(comp)
            db.session.commit()
        
        response = client.get(f'/api/compatibility/{u1_id}/{u2_id}/ui', headers={'Authorization': f'Bearer {token1}'})
        assert response.status_code == 200
    except Exception as e:
        print(f"DEBUG EXCEPTION UI: {e}")
        raise e
