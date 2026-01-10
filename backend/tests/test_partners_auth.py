
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
# Import the actual blueprint and models
from src.routes.partners import partners_bp
from src.models.partner import PartnerConnection
from src.models.survey import SurveySubmission, SurveyProgress
from src.models.profile import Profile
from src.extensions import db
import jwt
import os

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize DB
    db.init_app(app)
    
    # Register blueprint
    app.register_blueprint(partners_bp)
    
    # Create tables within application context
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

@pytest.fixture
def mock_conn_query():
    with patch('src.models.partner.PartnerConnection.query') as mock_query:
        yield mock_query

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_get_connections_unauthorized(client):
    # Missing header
    response = client.get('/api/partners/connections')
    assert response.status_code == 401
    
    # Invalid token
    response = client.get('/api/partners/connections', headers={'Authorization': 'Bearer invalid'})
    assert response.status_code == 401

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_get_connections_authorized(client, mock_user_query, mock_conn_query):
    # Mock Token
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = jwt.encode({"sub": user_id, "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
    
    # Mock User existence
    # Note: User model is imported in partners.py, so we patch User.query
    mock_user = MagicMock(id=user_id, email="test@example.com")
    mock_user_query.get.return_value = mock_user
    
    # Mock Connections
    # We simulate an empty list of connections
    mock_conn_query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
    
    response = client.get('/api/partners/connections', headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    mock_user_query.get.assert_called()

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_create_connection_request(client, mock_user_query):
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = jwt.encode({"sub": user_id, "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
    
    # Mock User existence (Requester)
    mock_user = MagicMock(id=user_id, email="requester@example.com")
    mock_user_query.filter_by.side_effect = lambda id=None, email=None: mock_user if (id or email) else None
    
    # For this test, we want to allow the Add operation to succeed.
    # Since we are using an in-memory DB for PartnerConnection but mocking User,
    # we need to be careful. The route does `User.query...` which is mocked.
    # But it does `PartnerConnection(...)` and `db.session.add()`.
    # `db.session` is real (SQLite). `PartnerConnection` is real (SQLite).
    # `User` is mocked.
    
    # However, PartnerConnection has ForeignKey to users.id. 
    # SQLite generally enforces FKs if enabled, but Flask-SQLAlchemy might not by default in sqlite.
    # If FK fails, we might get IntegrityError.
    
    # Strategy: Mock PartnerConnection.query so we don't need real DB state for existing checks,
    # BUT let the write go to the DB (or mock the commit).
    # Actually, simpler: patch `db.session` so we don't actually write to DB.
    
    with patch('src.routes.partners.PartnerConnection.query') as mock_pc_query, \
         patch('src.extensions.db.session') as mock_session:
        
        # Mock no existing connections
        mock_pc_query.filter.return_value.filter.return_value.all.return_value = []

        payload = {"recipient_email": "partner@example.com"}
        response = client.post('/api/partners/connect', 
                             json=payload,
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 201
        assert response.json['success'] is True
        mock_session.add.assert_called()
        mock_session.commit.assert_called()
