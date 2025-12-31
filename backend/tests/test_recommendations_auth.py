
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from backend.src.extensions import db
from backend.src.models.user import User
from backend.src.models.profile import Profile
from backend.src.models.session import Session
from backend.src.models.notification import PushNotificationToken
from backend.src.routes.recommendations import bp as recommendations_bp
from backend.src.routes.notifications import notifications_bp
import uuid
import os

# --- Fixtures ---

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Init DB
    db.init_app(app)
    
    # Register Blueprints
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(notifications_bp)
    
    # Create tables and Seed Data
    with app.app_context():
        db.create_all()
        
        u1_id_uuid = uuid.uuid4()
        u2_id_uuid = uuid.uuid4()
        
        # Strings
        u1_id = str(u1_id_uuid)
        u2_id = str(u2_id_uuid)
        
        u1 = User(id=u1_id_uuid, email="u1@e.com", display_name="User 1")
        u2 = User(id=u2_id_uuid, email="u2@e.com", display_name="User 2")
        db.session.add_all([u1, u2])
        db.session.commit()
        
        # Attach to app for tests to access
        app.u1_id = u1_id
        app.u2_id = u2_id
        
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def env_setup():
    with patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "testsecret"}):
        yield

# --- Mocks ---

@pytest.fixture
def mock_auth_success(app):
    with patch('backend.src.middleware.auth.jwt.decode') as mock_decode:
        # Use valid UUID from seeded user
        mock_decode.return_value = {"sub": app.u1_id, "aud": "authenticated", "exp": 9999999999}
        yield mock_decode

@pytest.fixture
def mock_auth_stranger():
    with patch('backend.src.middleware.auth.jwt.decode') as mock_decode:
        mock_decode.return_value = {"sub": str(uuid.uuid4()), "aud": "authenticated", "exp": 9999999999}
        yield mock_decode

# --- Tests ---

def test_create_rec_success_owner(client, mock_auth_success, app):
    """Test generating recs as owner of profile A."""
    with patch('backend.src.routes.recommendations.repository') as mock_repo:
        # Mock Profile A (Owner)
        mock_p1 = MagicMock()
        mock_p1.user_id = app.u1_id  # Matches mock_auth_success
        mock_p1.to_dict.return_value = {"activities": {}, "anatomy": {}}
        
        # Mock Profile B (Different user)
        mock_p2 = MagicMock()
        mock_p2.user_id = app.u2_id
        mock_p2.to_dict.return_value = {"activities": {}, "anatomy": {}}
        
        # Side effect for get_or_create_profile
        def side_effect(sub_id):
            if sub_id == "sub1": return mock_p1
            if sub_id == "sub2": return mock_p2
            return None
        mock_repo.get_or_create_profile.side_effect = side_effect
        
        mock_repo.find_best_activity_candidate.return_value = None 
        
        data = {
            "player_a": {"submission_id": "sub1"},
            "player_b": {"submission_id": "sub2"},
            "session": {"session_id": "newsess"}
        }
        res = client.post('/api/recommendations', json=data, headers={'Authorization': 'Bearer token'})
        
        assert res.status_code == 200

def test_create_rec_forbidden_stranger(client, mock_auth_stranger, app):
    """Test that stranger cannot use my submission_id."""
    with patch('backend.src.routes.recommendations.repository') as mock_repo:
        mock_p1 = MagicMock()
        mock_p1.user_id = app.u1_id # Owned by u1
        mock_p1.to_dict.return_value = {}
        
        mock_repo.get_or_create_profile.return_value = mock_p1
        
        data = {
            "player_a": {"submission_id": "sub1"}
        }
        res = client.post('/api/recommendations', json=data, headers={'Authorization': 'Bearer token'})
        assert res.status_code == 403

def test_get_rec_success(client, mock_auth_success, app):
    """Test get recs for valid session participant."""
    with patch('backend.src.routes.recommendations.repository') as mock_repo:
        mock_sess = MagicMock()
        mock_sess.session_id = "sess1"
        mock_sess.player_a_profile.user_id = app.u1_id # Match u1
        mock_sess.player_b_profile.user_id = app.u2_id
        mock_sess.primary_user_id = None
        mock_sess.partner_user_id = None
        mock_sess.session_owner_user_id = None
        
        mock_sess.to_dict.return_value = {"session_id": "sess1"}
        
        mock_repo.get_session.return_value = mock_sess
        mock_repo.get_session_activities.return_value = []
        
        res = client.get('/api/recommendations/sess1', headers={'Authorization': 'Bearer token'})
        assert res.status_code == 200

def test_get_rec_forbidden(client, mock_auth_stranger, app):
    """Test stranger cannot access session."""
    with patch('backend.src.routes.recommendations.repository') as mock_repo:
        mock_sess = MagicMock()
        mock_sess.session_id = "sess1"
        mock_sess.player_a_profile.user_id = app.u1_id
        mock_sess.player_b_profile.user_id = app.u2_id
        mock_sess.primary_user_id = None
        mock_sess.partner_user_id = None
        mock_sess.session_owner_user_id = None
        
        mock_repo.get_session.return_value = mock_sess
        
        res = client.get('/api/recommendations/sess1', headers={'Authorization': 'Bearer token'})
        assert res.status_code == 403

def test_notification_reg_success(client, mock_auth_success, app):
    """Test registering notification token."""
    # Using REAL DB, no patching of models
    data = {
        "user_id": app.u1_id, # Match authenticated user
        "device_token": "dev1_uniq",
        "platform": "ios"
    }
    res = client.post('/api/notifications/register', json=data, headers={'Authorization': 'Bearer token'})
    assert res.status_code == 201
    
    # Verify in DB
    with app.app_context():
        token = PushNotificationToken.query.filter_by(device_token="dev1_uniq").first()
        assert token is not None
        assert str(token.user_id) == app.u1_id

def test_notification_reg_forbidden(client, mock_auth_stranger, app):
    """Test registering notification token for OTHER user."""
    data = {
        "user_id": app.u1_id, # Target is u1
        "device_token": "dev2_uniq",
        "platform": "ios"
    }
    # Caller is stranger
    res = client.post('/api/notifications/register', json=data, headers={'Authorization': 'Bearer token'})
    assert res.status_code == 403
