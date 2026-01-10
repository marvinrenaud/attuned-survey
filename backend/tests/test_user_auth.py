import pytest
import jwt
import os
import uuid
from backend.src.models.user import User
from backend.src.extensions import db

@pytest.fixture
def auth_header():
    def _get_header(user_id):
        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
        return {'Authorization': f'Bearer {token}'}
    return _get_header

class TestUserAuthIntegration:
    """Integration tests for User Auth Routes using DB (No Mocks)."""

    def test_auth_profile_get_unauthorized(self, client):
        """Test getting profile without token fails."""
        response = client.get('/api/auth/profile')
        assert response.status_code == 401

    def test_auth_profile_get_authorized(self, client, app, auth_header):
        """Test getting profile with valid token succeeds."""
        user_id = uuid.uuid4()
        
        with app.app_context():
            user = User(id=user_id, email="real-db@example.com")
            db.session.add(user)
            db.session.commit()
        
        headers = auth_header(user_id)
        response = client.get('/api/auth/profile', headers=headers)
        
        assert response.status_code == 200
        assert response.json['user']['id'] == str(user_id)
        assert response.json['user']['email'] == "real-db@example.com"

    def test_user_legacy_get_ownership_enforced(self, client, app, auth_header):
        """Test user cannot access another user's legacy profile route."""
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()
        
        with app.app_context():
            user1 = User(id=user1_id, email="user1@test.com")
            user2 = User(id=user2_id, email="user2@test.com")
            db.session.add_all([user1, user2])
            db.session.commit()
        
        headers = auth_header(user1_id)
        
        # User 1 tries to access User 2
        # Note: Route /users/<id> is legacy/user_bp
        response = client.get(f'/users/{user2_id}', headers=headers)
        
        assert response.status_code == 403
        assert response.json['error'] == 'Unauthorized'

    def test_user_legacy_get_success(self, client, app, auth_header):
        """Test user can access their own legacy profile route."""
        user_id = uuid.uuid4()
        
        with app.app_context():
            user = User(id=user_id, email="legacy@test.com")
            # Ensure profile/submission isn't required for basic GET, or create if needed
            # The endpoint just returns user.to_dict() usually
            db.session.add(user)
            db.session.commit()
        
        headers = auth_header(user_id)
        response = client.get(f'/users/{user_id}', headers=headers)
        
        assert response.status_code == 200
        assert response.json['id'] == str(user_id)
