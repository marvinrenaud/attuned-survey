"""
Tests for guest mode gameplay - player name resolution and personalization.
"""
import pytest
from unittest.mock import patch
from flask import Flask
from src.routes.gameplay import gameplay_bp, _resolve_player
from src.models.user import User
from src.models.session import Session
from src.models.activity import Activity
from src.models.profile import Profile
from src.extensions import db
import os
import uuid
import jwt


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
        p_legacy = Profile(
            id=1, 
            submission_id="legacy",
            power_dynamic={},
            arousal_propensity={}, 
            domain_scores={},
            activities={},
            truth_topics={},
            boundaries={},
            anatomy={}
        )
        db.session.add(p_legacy)
        db.session.commit()
        
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def create_user(app, user_id, display_name="Test User", 
                has_penis=False, has_vagina=True, has_breasts=True,
                likes_penis=True, likes_vagina=False, likes_breasts=False):
    """Helper to create a user with specific anatomy."""
    with app.app_context():
        uid = uuid.UUID(user_id)
        user = User(
            id=uid, 
            email=f"{user_id[:8]}@test.com",
            display_name=display_name,
            has_penis=has_penis,
            has_vagina=has_vagina,
            has_breasts=has_breasts,
            likes_penis=likes_penis,
            likes_vagina=likes_vagina,
            likes_breasts=likes_breasts
        )
        db.session.add(user)
        db.session.commit()
        return user


class TestResolvePlayerHelper:
    """Unit tests for the _resolve_player helper function."""
    
    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
    def test_resolve_player_current_user_from_db(self, app):
        """Registered user should have name/anatomy resolved from DB."""
        user_id = str(uuid.uuid4())
        create_user(app, user_id, display_name="Alice", 
                   has_vagina=True, has_breasts=True, has_penis=False,
                   likes_penis=True)
        
        with app.app_context():
            result = _resolve_player({"id": user_id}, user_id)
            
            assert result["id"] == user_id
            assert result["name"] == "Alice"
            assert set(result["anatomy"]) == {"vagina", "breasts"}
            assert "penis" in result["anatomy_preference"]
    
    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
    def test_resolve_player_other_user_not_looked_up(self, app):
        """Other user IDs should NOT be looked up (IDOR protection)."""
        current_user = str(uuid.uuid4())
        other_user = str(uuid.uuid4())
        
        # Create the other user with specific data
        create_user(app, other_user, display_name="Secret User",
                   has_penis=True)
        
        with app.app_context():
            # Try to resolve the other user - should NOT get their DB data
            result = _resolve_player({"id": other_user}, current_user)
            
            # Should NOT have the DB display name (IDOR protection!)
            assert result["name"] != "Secret User"
            assert result["name"] == "Guest"  # Default for non-current-user
            assert result["anatomy"] == []  # Not from DB
    
    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
    def test_resolve_player_guest_uses_provided_values(self, app):
        """Guest players should use frontend-provided values."""
        current_user = str(uuid.uuid4())
        guest_id = str(uuid.uuid4())
        
        with app.app_context():
            result = _resolve_player({
                "id": guest_id,
                "name": "Guest Partner",
                "anatomy": ["penis"],
                "anatomy_preference": ["vagina", "breasts"]
            }, current_user)
            
            assert result["id"] == guest_id
            assert result["name"] == "Guest Partner"
            assert result["anatomy"] == ["penis"]
            assert result["anatomy_preference"] == ["vagina", "breasts"]
    
    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
    def test_resolve_player_guest_without_id_gets_generated_id(self, app):
        """Guest without ID should get a generated UUID."""
        current_user = str(uuid.uuid4())
        
        with app.app_context():
            result = _resolve_player({
                "name": "New Guest"
            }, current_user)
            
            # Should have a valid UUID
            assert result["id"] is not None
            uuid.UUID(result["id"])  # Should not raise
            assert result["name"] == "New Guest"
    
    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
    def test_resolve_player_json_encoded_string(self, app):
        """JSON-encoded guest player string should be parsed correctly."""
        import json
        current_user = str(uuid.uuid4())
        
        # Simulate what might happen if frontend sends JSON as a string
        guest_data = {"name": "JSON Guest", "anatomy": ["penis"], "anatomy_preference": ["vagina"]}
        json_string = json.dumps(guest_data)
        
        with app.app_context():
            result = _resolve_player(json_string, current_user)
            
            # Should have parsed the JSON and used its values
            assert result["name"] == "JSON Guest"
            assert result["anatomy"] == ["penis"]
            assert result["anatomy_preference"] == ["vagina"]


class TestStartGameGuestMode:
    """Integration tests for /api/game/start with guest players."""
    
    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
    def test_start_game_resolves_primary_user_name(self, client, app):
        """Primary user should have their display_name resolved."""
        user_id = str(uuid.uuid4())
        create_user(app, user_id, display_name="Primary Player")
        
        with app.app_context():
            # Add a test activity
            act = Activity(activity_id=1, type="truth", rating="R", intensity=1, 
                          script={'steps': [{'do': 'Test activity'}]}, is_active=True)
            db.session.add(act)
            db.session.commit()
        
        token = jwt.encode({"sub": user_id, "aud": "authenticated"}, 
                          "test_secret", algorithm="HS256")
        
        response = client.post('/api/game/start', 
            json={
                "players": [
                    {"id": user_id},
                    {"name": "Guest Partner", "anatomy": ["penis"]}
                ],
                "settings": {"intimacy_level": 3}
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.json
        
        # Check session was created with correct players
        with app.app_context():
            sess = Session.query.get(data['session_id'])
            players = sess.players
            
            # Primary player should have DB name
            assert players[0]["name"] == "Primary Player"
            
            # Guest should have provided name
            assert players[1]["name"] == "Guest Partner"
    
    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
    def test_start_game_resolves_primary_user_anatomy(self, client, app):
        """Primary user should have their anatomy resolved from DB."""
        user_id = str(uuid.uuid4())
        create_user(app, user_id, display_name="Test", 
                   has_vagina=True, has_breasts=True, has_penis=False,
                   likes_penis=True, likes_vagina=True)
        
        with app.app_context():
            act = Activity(activity_id=1, type="truth", rating="R", intensity=1, 
                          script={'steps': [{'do': 'Test'}]}, is_active=True)
            db.session.add(act)
            db.session.commit()
        
        token = jwt.encode({"sub": user_id, "aud": "authenticated"}, 
                          "test_secret", algorithm="HS256")
        
        response = client.post('/api/game/start', 
            json={
                "players": [
                    {"id": user_id},
                    {"name": "Guest", "anatomy": ["penis"], "anatomy_preference": ["vagina"]}
                ],
                "settings": {"intimacy_level": 3}
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        
        with app.app_context():
            sess = Session.query.get(response.json['session_id'])
            players = sess.players
            
            # Primary user anatomy from DB
            assert set(players[0]["anatomy"]) == {"vagina", "breasts"}
            assert set(players[0]["anatomy_preference"]) == {"penis", "vagina"}
            
            # Guest anatomy from request
            assert players[1]["anatomy"] == ["penis"]
            assert players[1]["anatomy_preference"] == ["vagina"]
    
    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test_secret"})
    def test_start_game_idor_protection(self, client, app):
        """Attempting to resolve another user's data should fail safely."""
        current_user = str(uuid.uuid4())
        victim_user = str(uuid.uuid4())
        
        # Create victim with sensitive data
        create_user(app, victim_user, display_name="Victim Name")
        # Create current user
        create_user(app, current_user, display_name="Attacker")
        
        with app.app_context():
            act = Activity(activity_id=1, type="truth", rating="R", intensity=1, 
                          script={'steps': [{'do': 'Test'}]}, is_active=True)
            db.session.add(act)
            db.session.commit()
        
        token = jwt.encode({"sub": current_user, "aud": "authenticated"}, 
                          "test_secret", algorithm="HS256")
        
        # Try to include victim's ID
        response = client.post('/api/game/start', 
            json={
                "players": [
                    {"id": current_user},
                    {"id": victim_user}  # Attempting to get victim's data
                ],
                "settings": {"intimacy_level": 3}
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        
        with app.app_context():
            sess = Session.query.get(response.json['session_id'])
            players = sess.players
            
            # Current user should have their name
            assert players[0]["name"] == "Attacker"
            
            # Victim's name should NOT be resolved (IDOR protection)
            assert players[1]["name"] != "Victim Name"
            assert players[1]["name"] == "Guest"  # Default fallback
