"""
Authentication and authorization tests for notification endpoints.
"""

import pytest
import uuid
import os
from unittest.mock import patch
import jwt

from backend.src.models.user import User
from backend.src.models.notification import PushNotificationToken
from backend.src.extensions import db


def create_token(user_id: str) -> str:
    """Create a valid JWT token for testing."""
    return jwt.encode(
        {"sub": str(user_id), "aud": "authenticated"},
        "test-secret-key",
        algorithm="HS256"
    )


def get_auth_headers(user_id: str) -> dict:
    """Get authorization headers for a user."""
    return {'Authorization': f'Bearer {create_token(user_id)}'}


class TestNotificationRegistration:
    """Test notification token registration endpoint."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_register_token_unauthorized(self, client):
        """Test that registration requires authentication."""
        response = client.post('/api/notifications/register', json={
            "user_id": str(uuid.uuid4()),
            "device_token": "test_token",
            "platform": "ios"
        })
        assert response.status_code == 401

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_register_token_forbidden_other_user(self, client, db_session):
        """Test that user cannot register token for another user (IDOR)."""
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()

        user_a = User(id=user_a_id, email="a@test.com")
        user_b = User(id=user_b_id, email="b@test.com")
        db_session.add_all([user_a, user_b])
        db_session.commit()

        # User A tries to register token for User B
        response = client.post('/api/notifications/register',
            json={
                "user_id": str(user_b_id),
                "device_token": "attacker_token",
                "platform": "ios"
            },
            headers=get_auth_headers(user_a_id)
        )
        assert response.status_code == 403

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_register_token_success(self, client, db_session):
        """Test successful token registration."""
        user_id = uuid.uuid4()
        user = User(id=user_id, email="user@test.com")
        db_session.add(user)
        db_session.commit()

        response = client.post('/api/notifications/register',
            json={
                "user_id": str(user_id),
                "device_token": "valid_token_123",
                "platform": "ios"
            },
            headers=get_auth_headers(user_id)
        )
        assert response.status_code == 201

        # Verify in DB
        token = db_session.query(PushNotificationToken).filter_by(
            device_token="valid_token_123"
        ).first()
        assert token is not None
        assert str(token.user_id) == str(user_id)


class TestMarkNotificationRead:
    """Test mark notification as read endpoints."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_mark_read_unauthorized(self, client):
        """Test that marking read requires authentication."""
        response = client.post('/api/notifications/mark-read/1')
        assert response.status_code == 401

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_mark_all_read_unauthorized(self, client):
        """Test that marking all read requires authentication."""
        response = client.post('/api/notifications/mark-all-read')
        assert response.status_code == 401
