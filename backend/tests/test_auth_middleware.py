
import pytest
from flask import Flask, jsonify
from unittest.mock import patch, MagicMock 
import jwt
import os
from src.middleware.auth import token_required, optional_token

# Helper to create a test app
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    @app.route('/protected')
    @token_required
    def protected_route(user_id):
        return jsonify({'message': 'Success', 'user_id': user_id})

    @app.route('/optional')
    @optional_token
    def optional_route(user_id):
        if user_id:
             return jsonify({'message': 'Authenticated', 'user_id': user_id})
        return jsonify({'message': 'Anonymous'})
        
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_missing_header(client):
    response = client.get('/protected')
    assert response.status_code == 401
    assert "Authentication required" in response.json['error']

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_invalid_header_format(client):
    response = client.get('/protected', headers={'Authorization': 'InvalidFormat'})
    assert response.status_code == 401
    assert "Authentication required" in response.json['error']

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_valid_token(client):
    # Generate a valid token signed with test_secret
    token = jwt.encode(
        {"sub": "user-123", "aud": "authenticated"}, 
        "test_secret", 
        algorithm="HS256"
    )
    
    response = client.get('/protected', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.json['user_id'] == 'user-123'

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_token_missing_sub(client):
    # Token without user ID
    token = jwt.encode(
        {"aud": "authenticated"}, 
        "test_secret", 
        algorithm="HS256"
    )
    response = client.get('/protected', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 401
    assert "No user ID found" in response.json['message']

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_wrong_audience(client):
    # Token with wrong audience
    token = jwt.encode(
        {"sub": "user-123", "aud": "other_app"}, 
        "test_secret", 
        algorithm="HS256"
    )
    response = client.get('/protected', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 401
    assert "Invalid audience" in response.json['message']

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_optional_auth_anonymous(client):
    response = client.get('/optional')
    assert response.status_code == 200
    assert response.json['message'] == 'Anonymous'

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_optional_auth_logged_in(client):
    token = jwt.encode(
        {"sub": "user-456", "aud": "authenticated"}, 
        "test_secret", 
        algorithm="HS256"
    )
    response = client.get('/optional', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert response.json['message'] == 'Authenticated'
    assert response.json['user_id'] == 'user-456'
