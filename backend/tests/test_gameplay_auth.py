
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.routes.gameplay import gameplay_bp
from src.models.user import User
from src.models.session import Session
from src.models.activity import Activity
from src.models.profile import Profile
from src.models.activity_history import UserActivityHistory  # Required for db.create_all()
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
    app.register_blueprint(gameplay_bp)
    
    with app.app_context():
        db.create_all()
        # Seed legacy profile for Session FK
        p1 = Profile(
            id=1, 
            user_id=None, 
            submission_id="legacy",
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
        db.session.add(p1)
        db.session.commit()
        
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_start_game_unauthorized(client):
    response = client.post('/api/game/start', json={})
    assert response.status_code == 401

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_start_game_success(client, app):
    user_id = str(uuid.uuid4())
    token = jwt.encode({"sub": user_id, "aud": "authenticated"}, "test_secret", algorithm="HS256")
    
    with app.app_context():
        # Setup User, Activity
        user = User(id=uuid.UUID(user_id), email="player@example.com")
        db.session.add(user)
        
        act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps':[]})
        db.session.add(act)
        db.session.commit()
        
    response = client.post('/api/game/start', 
                           json={"player_ids": []}, 
                           headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    data = response.json
    assert 'session_id' in data
    
    # Verify owner_id logic: user_id should be in players
    with app.app_context():
        sess = Session.query.get(data['session_id'])
        assert sess is not None
        players = sess.players
        player_ids = [str(p['id']) for p in players]
        assert user_id in player_ids

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_next_turn_unauthorized(client):
    response = client.post('/api/game/SESSION_ID/next', json={})
    assert response.status_code == 401

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_next_turn_forbidden(client, app):
    # User 1 creates session, User 2 tries to play
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())
    token2 = jwt.encode({"sub": user2_id, "aud": "authenticated"}, "test_secret", algorithm="HS256")
    
    session_id = "test_sess"
    
    with app.app_context():
        sess = Session(
            session_id=session_id,
            players=[{'id': user1_id, 'name': 'P1'}],
            game_settings={},
            current_turn_state={'queue': []},
            player_a_profile_id=1,
            player_b_profile_id=1
        )
        db.session.add(sess)
        db.session.commit()
        
    response = client.post(f'/api/game/{session_id}/next', 
                           json={},
                           headers={'Authorization': f'Bearer {token2}'})
    
    assert response.status_code == 403

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
def test_next_turn_success(client, app):
    user_id = str(uuid.uuid4())
    token = jwt.encode({"sub": user_id, "aud": "authenticated"}, "test_secret", algorithm="HS256")
    session_id = str(uuid.uuid4())
    
    with app.app_context():
        user = User(id=uuid.UUID(user_id), email="p1@e.com")
        db.session.add(user)
        
        act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps':[]})
        db.session.add(act)
        
        # Create session with queue
        sess = Session(
            session_id=session_id,
            players=[{'id': user_id, 'name': 'P1'}],
            game_settings={},
            current_turn_state={
                'queue': [{
                    'card': {'type': 'TRUTH', 'card_id': '1'},
                    'primary_player_idx': 0,
                    'status': 'SHOW_CARD',
                    'step': 1,
                    'card_id': '1'
                }]
            },
            player_a_profile_id=1,
            player_b_profile_id=1
        )
        db.session.add(sess)
        db.session.commit()
        
    response = client.post(f'/api/game/{session_id}/next',
                           json={},
                           headers={'Authorization': f'Bearer {token}'})
                           
    assert response.status_code == 200
    json_resp = response.json
    assert json_resp['session_id'] == session_id
