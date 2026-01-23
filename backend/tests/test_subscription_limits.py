"""
Tests for lifetime activity limits (replacing daily limits).

TDD: These tests are written BEFORE implementation.
The existing endpoints need to be updated to use lifetime_activity_count
instead of daily_activity_count.
"""
import os
import pytest
import uuid
from datetime import datetime
from unittest.mock import patch

from src.models.user import User


@pytest.fixture
def app_context(app):
    """Ensure app context is pushed"""
    with app.app_context():
        yield


@pytest.fixture
def free_user(db_session, test_user_data):
    """Create a free tier user for testing"""
    user = User(
        id=test_user_data['id'],
        email=test_user_data['email'],
        display_name=test_user_data['display_name'],
        auth_provider=test_user_data['auth_provider'],
        demographics=test_user_data['demographics'],
        subscription_tier='free',
        daily_activity_count=0,
        daily_activity_reset_at=datetime.utcnow(),
        lifetime_activity_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def premium_user(db_session):
    """Create a premium tier user for testing"""
    user = User(
        id=uuid.uuid4(),
        email=f'premium-{uuid.uuid4().hex[:8]}@test.com',
        display_name='Premium User',
        auth_provider='email',
        demographics={},
        subscription_tier='premium',
        lifetime_activity_count=100,  # Even with high count, no limit for premium
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestLifetimeActivityLimits:
    """Tests for lifetime activity limit enforcement."""

    def test_check_limit_free_user_under_limit(self, client, app_context, free_user, db_session):
        """Free user with 5/10 activities shows remaining=5"""
        free_user.lifetime_activity_count = 5
        db_session.commit()

        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(free_user.id)}

            response = client.get(
                f'/api/subscriptions/check-limit/{free_user.id}',
                headers={'Authorization': 'Bearer valid-token'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['has_limit'] is True
            assert data['limit_reached'] is False
            assert data['activities_used'] == 5
            assert data['limit'] == 10
            assert data['remaining'] == 5

    def test_check_limit_free_user_at_limit(self, client, app_context, free_user, db_session):
        """Free user with 10/10 shows limit_reached=true"""
        free_user.lifetime_activity_count = 10
        db_session.commit()

        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(free_user.id)}

            response = client.get(
                f'/api/subscriptions/check-limit/{free_user.id}',
                headers={'Authorization': 'Bearer valid-token'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['has_limit'] is True
            assert data['limit_reached'] is True
            assert data['activities_used'] == 10
            assert data['remaining'] == 0

    def test_check_limit_premium_user_no_limit(self, client, app_context, premium_user, db_session):
        """Premium user shows has_limit=false regardless of count"""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(premium_user.id)}

            response = client.get(
                f'/api/subscriptions/check-limit/{premium_user.id}',
                headers={'Authorization': 'Bearer valid-token'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['has_limit'] is False
            assert data['limit_reached'] is False
            # Premium users have no limit, so remaining is -1 (unlimited)
            assert data['remaining'] == -1

    def test_increment_increases_lifetime_count(self, client, app_context, free_user, db_session):
        """POST increments lifetime_activity_count for free users"""
        free_user.lifetime_activity_count = 3
        db_session.commit()

        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(free_user.id)}

            response = client.post(
                f'/api/subscriptions/increment-activity/{free_user.id}',
                headers={'Authorization': 'Bearer valid-token'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['lifetime_activity_count'] == 4

            # Verify DB update
            db_session.refresh(free_user)
            assert free_user.lifetime_activity_count == 4

    def test_increment_premium_user_no_change(self, client, app_context, premium_user, db_session):
        """Premium user increment is tracked but no limit enforced"""
        original_count = premium_user.lifetime_activity_count

        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(premium_user.id)}

            response = client.post(
                f'/api/subscriptions/increment-activity/{premium_user.id}',
                headers={'Authorization': 'Bearer valid-token'}
            )

            assert response.status_code == 200

            # Premium users don't increment (per design - they have unlimited)
            db_session.refresh(premium_user)
            assert premium_user.lifetime_activity_count == original_count


class TestSubscriptionStatus:
    """Tests for enhanced subscription status endpoint."""

    def test_status_free_user(self, client, app_context, free_user, db_session):
        """Status returns correct lifetime limit info for free user"""
        free_user.lifetime_activity_count = 7
        db_session.commit()

        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(free_user.id)}

            response = client.get(
                f'/api/subscriptions/status/{free_user.id}',
                headers={'Authorization': 'Bearer valid-token'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['subscription_tier'] == 'free'
            assert data['is_premium'] is False
            assert data['activities_used'] == 7
            assert data['activities_limit'] == 10
            assert data['activities_remaining'] == 3

    def test_status_premium_user(self, client, app_context, premium_user, db_session):
        """Status returns no limit info for premium user"""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(premium_user.id)}

            response = client.get(
                f'/api/subscriptions/status/{premium_user.id}',
                headers={'Authorization': 'Bearer valid-token'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['subscription_tier'] == 'premium'
            assert data['is_premium'] is True
            # Premium users have no limits
            assert data['activities_limit'] is None
            assert data['activities_remaining'] is None


class TestAuthorizationChecks:
    """Auth tests for subscription endpoints (401/403)."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_check_limit_unauthorized(self, client):
        """401 when no auth token provided"""
        response = client.get(f'/api/subscriptions/check-limit/{uuid.uuid4()}')
        assert response.status_code == 401

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_increment_unauthorized(self, client):
        """401 when no auth token provided"""
        response = client.post(f'/api/subscriptions/increment-activity/{uuid.uuid4()}')
        assert response.status_code == 401

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_status_unauthorized(self, client):
        """401 when no auth token provided"""
        response = client.get(f'/api/subscriptions/status/{uuid.uuid4()}')
        assert response.status_code == 401

    def test_check_limit_wrong_user(self, client, app_context, free_user, db_session):
        """403 when trying to check another user's limits"""
        other_user_id = uuid.uuid4()

        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(free_user.id)}

            response = client.get(
                f'/api/subscriptions/check-limit/{other_user_id}',
                headers={'Authorization': 'Bearer valid-token'}
            )

            assert response.status_code == 403
