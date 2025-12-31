
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.routes.survey import bp as survey_bp
from src.models.survey import SurveySubmission, SurveyBaseline
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
    app.register_blueprint(survey_bp)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_get_submissions_unauthorized(client):
    response = client.get('/api/survey/submissions')
    assert response.status_code == 401

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_get_submissions_authorized(client, app):
    user_id = str(uuid.uuid4())
    token = jwt.encode({"sub": user_id, "aud": "authenticated"}, "test_secret", algorithm="HS256")
    
    response = client.get('/api/survey/submissions', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert 'submissions' in response.json

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_get_compatibility_unauthorized(client):
    response = client.get('/api/survey/compatibility/a/b')
    assert response.status_code == 401

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_get_baseline_unauthorized(client):
    response = client.get('/api/survey/baseline')
    assert response.status_code == 401
