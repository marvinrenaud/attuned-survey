import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.routes.gameplay import gameplay_bp
from src.models.user import User
from src.models.session import Session
from src.models.activity import Activity
from src.models.profile import Profile
from src.extensions import db
import jwt
import os
import uuid
from datetime import datetime

# Local fixtures removed to use conftest.py's shared fixtures (with SQLite hooks)

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_start_game_unauthorized(client):
    response = client.post('/api/game/start', json={})
    assert response.status_code == 401

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_start_game_success(client, app, db_session):
    user_id = uuid.uuid4()
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
    
    # Use db_session for data setup
    user = User(id=user_id, email="player@example.com")
    db_session.add(user)
    
    act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps':[]})
    db_session.add(act)
    db_session.commit()
        
    response = client.post('/api/game/start', 
                           json={"player_ids": []}, 
                           headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    data = response.json
    assert 'session_id' in data
    
    # Verification using db_session
    sess = db_session.get(Session, data['session_id'])
    assert sess is not None
    players = sess.players
    player_ids = [str(p['id']) for p in players]
    assert str(user_id) in player_ids

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_next_turn_unauthorized(client):
    response = client.post('/api/game/SESSION_ID/next', json={})
    assert response.status_code == 401

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_next_turn_forbidden(client, app, db_session):
    # User 1 creates session, User 2 tries to play
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    token2 = jwt.encode({"sub": str(user2_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
    
    session_id = "test_sess"
    
    sess = Session(
        session_id=session_id,
        players=[{'id': str(user1_id), 'name': 'P1'}],
        game_settings={},
        current_turn_state={'queue': []},
        player_a_profile_id=1,
        player_b_profile_id=1
    )
    db_session.add(sess)
    db_session.commit()
        
    response = client.post(f'/api/game/{session_id}/next', 
                           json={},
                           headers={'Authorization': f'Bearer {token2}'})
    
    assert response.status_code == 403

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_next_turn_success(client, app, db_session):
    user_id = uuid.uuid4()
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
    session_id = str(uuid.uuid4())
    
    user = User(id=user_id, email="p1@e.com")
    db_session.add(user)
    
    act = Activity(activity_id=1, type="truth", rating="G", intensity=1, script={'steps':[]})
    db_session.add(act)
    
    # Create session with queue
    sess = Session(
        session_id=session_id,
        players=[{'id': str(user_id), 'name': 'P1'}],
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
        player_b_profile_id=1,
        session_owner_user_id=user_id # Ensure owner is linked for strict checks
    )
    db_session.add(sess)
    db_session.commit()
        
    response = client.post(f'/api/game/{session_id}/next',
                           json={},
                           headers={'Authorization': f'Bearer {token}'})
                           
    assert response.status_code == 200
    json_resp = response.json
    assert json_resp['session_id'] == session_id
