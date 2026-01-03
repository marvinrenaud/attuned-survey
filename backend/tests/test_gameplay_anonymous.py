
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.routes.gameplay import gameplay_bp
from src.extensions import db
from src.models.session import Session
from src.models.user import User
from src.models.activity_history import UserActivityHistory
import uuid
import os
import json

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    app.register_blueprint(gameplay_bp)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_db_session():
    with patch('src.extensions.db.session') as mock:
        yield mock

@pytest.fixture
def mock_history_count():
    with patch('src.routes.gameplay.db.session.execute') as mock_exec:
        yield mock_exec

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_start_game_anonymous_success(client):
    """Test starting a game as an anonymous guest with valid payload."""
    guest_uuid = str(uuid.uuid4())
    partner_uuid = str(uuid.uuid4())
    
    payload = {
        "anonymous_session_id": guest_uuid,
        "players": [
            {
                "id": guest_uuid,
                "name": "Guest 1",
                "anatomy": ["penis"]
            },
            {
                "id": partner_uuid,
                "name": "Guest 2", 
                "anatomy": ["vagina"]
            }
        ],
        "settings": {
            "intimacy_level": 3
        }
    }
    
    with patch('src.routes.gameplay._fill_queue') as mock_fill:
        mock_fill.return_value = [{"card": {"type": "TRUTH", "card_id": "1"}, "step": 1}]
        
        response = client.post('/api/game/start', 
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.json
        assert 'session_id' in data
        assert data['queue'][0]['card']['type'] == 'TRUTH'

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_start_game_missing_identity(client):
    """Test starting a game without token OR anonymous_session_id."""
    payload = {
        "players": [], # Missing anon ID
        "settings": {}
    }
    
    response = client.post('/api/game/start', 
                         data=json.dumps(payload),
                         content_type='application/json')
    
    # Expect 401 because no auth method provided
    assert response.status_code == 401

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_next_turn_anonymous_limit_reached(client):
    """Test that anonymous limit enforcement blocks play."""
    session_id = str(uuid.uuid4())
    guest_uuid = str(uuid.uuid4())
    
    # Mock Session finding
    with patch('src.models.session.Session.query') as mock_query:
        mock_session = MagicMock()
        mock_session.session_id = session_id
        # Participant check relies on players list
        mock_session.players = [{"id": guest_uuid, "name": "Guest"}]
        mock_session.current_turn_state = {"queue": [{"card": {"type": "TRUTH"}}]}
        
        mock_query.get.return_value = mock_session
        
        # Mock Limit Check to return TRUE (Limit Reached)
        with patch('src.routes.gameplay._check_daily_limit') as mock_limit:
            mock_limit.return_value = {
                "limit_reached": True,
                "used": 25,
                "limit": 25
            }
            
            # Mock queue scrubbing
            with patch('src.routes.gameplay._fill_queue', return_value=[]) as mock_fill:
                with patch('src.routes.gameplay._scrub_queue_for_limit') as mock_scrub:
                    mock_scrub.return_value = [{"card": {"type": "LIMIT_REACHED"}}]
                    
                    payload = {
                        "action": "NEXT",
                        "anonymous_session_id": guest_uuid
                    }
                    
                    response = client.post(f'/api/game/{session_id}/next',
                                         data=json.dumps(payload),
                                         content_type='application/json')
                    
                    assert response.status_code == 200
                    assert response.json['limit_status']['limit_reached'] is True
                    assert response.json['queue'][0]['card']['type'] == 'LIMIT_REACHED'
