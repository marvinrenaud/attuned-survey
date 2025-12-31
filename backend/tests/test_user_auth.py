
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.routes.auth import auth_bp
from src.routes.user import user_bp
from src.models.user import User
from src.extensions import db
import jwt
import os
import uuid

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_user_query():
    with patch('src.models.user.User.query') as mock_query:
        yield mock_query

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_auth_profile_get_unauthorized(client):
    response = client.get('/api/auth/profile')
    assert response.status_code == 401

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_auth_profile_get_authorized(client, mock_user_query):
    user_id = str(uuid.uuid4())
    token = jwt.encode({"sub": user_id, "aud": "authenticated"}, "test_secret", algorithm="HS256")
    
    mock_user = MagicMock(id=user_id, email="me@example.com")
    mock_user.to_dict.return_value = {'id': user_id, 'email': 'me@example.com'}
    mock_user_query.filter_by.return_value.first.return_value = mock_user
    
    response = client.get('/api/auth/profile', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.json['user']['id'] == user_id

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_user_legacy_get_ownership_enforced(client, mock_user_query):
    my_id = str(uuid.uuid4())
    other_id = str(uuid.uuid4())
    token = jwt.encode({"sub": my_id, "aud": "authenticated"}, "test_secret", algorithm="HS256")
    
    # Try to access other user's data
    response = client.get(f'/users/{other_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    assert response.json['error'] == 'Unauthorized'

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_user_legacy_get_success(client, mock_user_query):
    my_id = str(uuid.uuid4())
    token = jwt.encode({"sub": my_id, "aud": "authenticated"}, "test_secret", algorithm="HS256")
    
    mock_user = MagicMock(id=my_id)
    mock_user.to_dict.return_value = {'id': my_id}
    mock_user_query.filter_by.return_value.first_or_404.return_value = mock_user
    
    response = client.get(f'/users/{my_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.json['id'] == my_id
