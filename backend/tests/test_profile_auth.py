
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from datetime import datetime, timedelta, timezone
from backend.src.routes.profile_ui import bp as profile_ui_bp
from backend.src.routes.profile_sharing import profile_sharing_bp
from backend.src.extensions import db
from backend.src.models.user import User
from backend.src.models.profile import Profile
from backend.src.models.partner import PartnerConnection
import uuid
import os

# --- Fixtures ---

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    app.register_blueprint(profile_ui_bp)
    app.register_blueprint(profile_sharing_bp)
    
    with app.app_context():
        db.create_all()
        
        # Seed
        u1 = User(id=uuid.uuid4(), email="u1@e.com", display_name="User 1")
        u2 = User(id=uuid.uuid4(), email="u2@e.com", display_name="User 2")
        db.session.add_all([u1, u2])
        db.session.commit()
        
        # Profile
        p1 = Profile(user_id=u1.id, submission_id="sub1", profile_version="0.4", power_dynamic={}, arousal_propensity={}, domain_scores={}, activities={}, truth_topics={}, boundaries={}, anatomy={}, activity_tags={})
        db.session.add(p1)
        db.session.commit()
        
        app.u1_id = str(u1.id)
        app.u2_id = str(u2.id)
        
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def env_setup():
    with patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "testsecret"}):
        yield

@pytest.fixture
def mock_auth_success(app):
    with patch('backend.src.middleware.auth.jwt.decode') as mock_decode:
        mock_decode.return_value = {"sub": app.u1_id, "aud": "authenticated", "exp": 9999999999}
        yield mock_decode

@pytest.fixture
def mock_auth_u2(app):
    with patch('backend.src.middleware.auth.jwt.decode') as mock_decode:
        mock_decode.return_value = {"sub": app.u2_id, "aud": "authenticated", "exp": 9999999999}
        yield mock_decode

# --- Tests ---

def test_profile_ui_access(client, mock_auth_success):
    """Test accessing OWN profile UI (token derived)."""
    # Route: /api/users/profile-ui
    res = client.get('/api/users/profile-ui', headers={'Authorization': 'Bearer token'})
    assert res.status_code == 200
    assert res.json['display_name'] == "User 1"

def test_profile_sharing_settings(client, mock_auth_success):
    """Test accessing OWN sharing settings."""
    # Route: /api/profile-sharing/settings
    res = client.get('/api/profile-sharing/settings', headers={'Authorization': 'Bearer token'})
    assert res.status_code == 200
    assert res.json['user_id'] == client.application.u1_id

def test_update_sharing_settings(client, mock_auth_success):
    """Test updating OWN sharing settings."""
    data = {"profile_sharing_setting": "demographics_only"}
    res = client.put('/api/profile-sharing/settings', json=data, headers={'Authorization': 'Bearer token'})
    assert res.status_code == 200
    assert res.json['profile_sharing_setting'] == "demographics_only"

def test_partner_profile_access(client, mock_auth_u2, app):
    """Test accessing partner profile (User 2 requests User 1)."""
    # User 2 requests User 1.
    # Route: /api/profile-sharing/partner-profile/<partner_id>
    # Token matches requester (U2).

    # SECURITY: Must have partner relationship to access profile
    with app.app_context():
        # Create accepted partner connection between U2 and U1
        connection = PartnerConnection(
            requester_user_id=uuid.UUID(app.u2_id),
            recipient_user_id=uuid.UUID(app.u1_id),
            recipient_email="u1@e.com",
            status='accepted',
            connection_token=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1)
        )
        db.session.add(connection)
        db.session.commit()

    # Now with relationship established, access should succeed
    res = client.get(f'/api/profile-sharing/partner-profile/{app.u1_id}', headers={'Authorization': 'Bearer token'})
    assert res.status_code == 200
    assert res.json['display_name'] == "User 1"
