"""
IDOR (Insecure Direct Object Reference) Security Tests

These tests verify that users cannot access or modify resources belonging to other users.
Each test creates two users and verifies that User A cannot access User B's resources.

CRITICAL: All these tests MUST pass. Failures indicate security vulnerabilities.
"""

import pytest
import jwt
import uuid
import os
from unittest.mock import patch
from datetime import datetime, timedelta

from backend.src.models.user import User
from backend.src.models.partner import PartnerConnection, RememberedPartner
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


@pytest.fixture
def two_users(db_session):
    """Create two separate users for IDOR testing."""
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    user_a = User(
        id=user_a_id,
        email="user_a@test.com",
        display_name="User A",
        subscription_tier='free',
        daily_activity_count=5,
        daily_activity_reset_at=datetime.utcnow()
    )
    user_b = User(
        id=user_b_id,
        email="user_b@test.com",
        display_name="User B",
        subscription_tier='premium',
        daily_activity_count=10,
        daily_activity_reset_at=datetime.utcnow()
    )

    db_session.add_all([user_a, user_b])
    db_session.commit()

    return {
        'user_a': user_a,
        'user_b': user_b,
        'user_a_id': user_a_id,
        'user_b_id': user_b_id
    }


# =============================================================================
# SUBSCRIPTIONS IDOR TESTS
# =============================================================================

class TestSubscriptionsIDOR:
    """Test that subscription endpoints enforce ownership."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_validate_subscription_forbidden_other_user(self, client, db_session, two_users):
        """
        CRITICAL: User A cannot validate User B's subscription.

        Endpoint: GET /api/subscriptions/validate/<user_id>
        Expected: 403 Forbidden when user_id doesn't match authenticated user
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # User A tries to validate User B's subscription
        response = client.get(
            f'/api/subscriptions/validate/{user_b_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"SECURITY VULNERABILITY: User can access another user's subscription validation. Got {response.status_code}"
        assert 'error' in response.json or 'message' in response.json

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_check_limit_forbidden_other_user(self, client, db_session, two_users):
        """
        CRITICAL: User A cannot check User B's daily limits.

        Endpoint: GET /api/subscriptions/check-limit/<user_id>
        Expected: 403 Forbidden when user_id doesn't match authenticated user
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # User A tries to check User B's limits
        response = client.get(
            f'/api/subscriptions/check-limit/{user_b_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"SECURITY VULNERABILITY: User can check another user's daily limits. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_increment_activity_forbidden_other_user(self, client, db_session, two_users):
        """
        CRITICAL: User A cannot increment User B's activity count.

        Endpoint: POST /api/subscriptions/increment-activity/<user_id>
        Expected: 403 Forbidden when user_id doesn't match authenticated user
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']
        initial_count = two_users['user_b'].daily_activity_count

        # User A tries to increment User B's counter
        response = client.post(
            f'/api/subscriptions/increment-activity/{user_b_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"SECURITY VULNERABILITY: User can increment another user's activity count. Got {response.status_code}"

        # Verify count wasn't modified
        db_session.refresh(two_users['user_b'])
        assert two_users['user_b'].daily_activity_count == initial_count, \
            "SECURITY VULNERABILITY: Activity count was modified despite 403"


# =============================================================================
# USERS ENDPOINT IDOR TESTS
# =============================================================================

class TestUsersIDOR:
    """Test that user endpoints enforce ownership."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_update_user_forbidden_other_user(self, client, db_session, two_users):
        """
        CRITICAL: User A cannot update User B's profile.

        Endpoint: PUT /users/<user_id>
        Expected: 403 Forbidden when user_id doesn't match authenticated user
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']
        original_name = two_users['user_b'].display_name

        # User A tries to update User B's profile
        response = client.put(
            f'/users/{user_b_id}',
            json={'display_name': 'HACKED'},
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"SECURITY VULNERABILITY: User can update another user's profile. Got {response.status_code}"

        # Verify name wasn't modified
        db_session.refresh(two_users['user_b'])
        assert two_users['user_b'].display_name == original_name, \
            "SECURITY VULNERABILITY: Display name was modified despite 403"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_delete_user_forbidden_other_user(self, client, db_session, two_users):
        """
        CRITICAL: User A cannot delete User B's account.

        Endpoint: DELETE /users/<user_id>
        Expected: 403 Forbidden when user_id doesn't match authenticated user
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # User A tries to delete User B's account
        response = client.delete(
            f'/users/{user_b_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"SECURITY VULNERABILITY: User can delete another user's account. Got {response.status_code}"

        # Verify user wasn't deleted
        user_b = db_session.get(User, two_users['user_b_id'])
        assert user_b is not None, \
            "SECURITY VULNERABILITY: User was deleted despite 403"


# =============================================================================
# PARTNERS ENDPOINT IDOR TESTS
# =============================================================================

class TestPartnersIDOR:
    """Test that partner endpoints enforce ownership."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_decline_connection_forbidden_wrong_recipient(self, client, db_session, two_users):
        """
        CRITICAL: User A cannot decline a connection request sent to User B.

        Endpoint: POST /api/partners/connections/<id>/decline
        Expected: 403 Forbidden when caller is not the recipient
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']
        user_c_id = uuid.uuid4()

        # Create User C (the attacker)
        user_c = User(id=user_c_id, email="attacker@test.com")
        db_session.add(user_c)

        # Create connection: A requests B
        connection = PartnerConnection(
            requester_user_id=user_a_id,
            recipient_user_id=user_b_id,
            recipient_email="user_b@test.com",
            status='pending',
            connection_token=str(uuid.uuid4()),
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        db_session.add(connection)
        db_session.commit()

        connection_id = connection.id

        # User C (not the recipient) tries to decline
        response = client.post(
            f'/api/partners/connections/{connection_id}/decline',
            headers=get_auth_headers(user_c_id)
        )

        assert response.status_code == 403, \
            f"SECURITY VULNERABILITY: Non-recipient can decline connection. Got {response.status_code}"

        # Verify connection status unchanged
        db_session.refresh(connection)
        assert connection.status == 'pending', \
            "SECURITY VULNERABILITY: Connection status changed despite 403"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_accept_connection_forbidden_wrong_recipient(self, client, db_session, two_users):
        """
        CRITICAL: User C cannot accept a connection request sent to User B.

        Endpoint: POST /api/partners/connections/<id>/accept
        Expected: 403 Forbidden when caller is not the recipient
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']
        user_c_id = uuid.uuid4()

        # Create User C (the attacker)
        user_c = User(id=user_c_id, email="attacker2@test.com")
        db_session.add(user_c)

        # Create connection: A requests B
        connection = PartnerConnection(
            requester_user_id=user_a_id,
            recipient_user_id=user_b_id,
            recipient_email="user_b@test.com",
            status='pending',
            connection_token=str(uuid.uuid4()),
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        db_session.add(connection)
        db_session.commit()

        connection_id = connection.id

        # User C (not the recipient) tries to accept
        response = client.post(
            f'/api/partners/connections/{connection_id}/accept',
            headers=get_auth_headers(user_c_id)
        )

        assert response.status_code == 403, \
            f"SECURITY VULNERABILITY: Non-recipient can accept connection. Got {response.status_code}"

        # Verify connection status unchanged
        db_session.refresh(connection)
        assert connection.status == 'pending', \
            "SECURITY VULNERABILITY: Connection status changed despite 403"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_delete_remembered_partner_forbidden_other_user(self, client, db_session, two_users):
        """
        CRITICAL: User A cannot delete User B's remembered partner.

        Endpoint: DELETE /api/partners/remembered/<partner_user_id>
        Expected: 403 Forbidden when trying to delete another user's remembered partner

        Note: This endpoint deletes from the CALLER's remembered partners list,
        so we need to verify User A can't manipulate User B's list.
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']
        user_c_id = uuid.uuid4()

        # Create User C
        user_c = User(id=user_c_id, email="partner_c@test.com")
        db_session.add(user_c)

        # User B has User C as remembered partner
        remembered = RememberedPartner(
            user_id=user_b_id,
            partner_user_id=user_c_id,
            partner_name="Partner C",
            partner_email="partner_c@test.com"
        )
        db_session.add(remembered)
        db_session.commit()

        # User A tries to remove C from B's remembered list
        # The endpoint is /api/partners/remembered/<partner_user_id>
        # It should only affect the AUTHENTICATED user's list
        response = client.delete(
            f'/api/partners/remembered/{user_c_id}',
            headers=get_auth_headers(user_a_id)
        )

        # This should either 404 (not found in A's list) or succeed silently
        # But B's list should remain intact

        # Verify B's remembered partner wasn't deleted
        remaining = db_session.query(RememberedPartner).filter_by(
            user_id=user_b_id,
            partner_user_id=user_c_id
        ).first()

        assert remaining is not None, \
            "SECURITY VULNERABILITY: User A's action deleted User B's remembered partner"


# =============================================================================
# AUTH PROFILE IDOR TESTS
# =============================================================================

class TestAuthProfileIDOR:
    """Test that auth profile endpoints enforce ownership."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_patch_profile_forbidden_other_user(self, client, db_session, two_users):
        """
        CRITICAL: User A cannot modify User B's auth profile.

        Endpoint: PATCH /api/auth/profile
        Note: This endpoint uses the token's user_id, so IDOR is less likely,
        but we verify the endpoint doesn't accept a user_id parameter that overrides.
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']
        original_name = two_users['user_b'].display_name

        # User A authenticated, but tries to pass user_b_id in body
        response = client.patch(
            '/api/auth/profile',
            json={
                'user_id': str(user_b_id),  # Attempt to override target
                'display_name': 'HACKED'
            },
            headers=get_auth_headers(user_a_id)
        )

        # The endpoint should use token's user_id, not body's user_id
        # So this should modify A's profile, not B's

        # Verify B's name wasn't modified
        db_session.refresh(two_users['user_b'])
        assert two_users['user_b'].display_name == original_name, \
            "SECURITY VULNERABILITY: Attacker modified another user's profile via user_id parameter"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_delete_profile_forbidden_other_user(self, client, db_session, two_users):
        """
        CRITICAL: User A cannot delete User B's auth profile.

        Endpoint: DELETE /api/auth/profile
        Note: Similar to PATCH, this should use token's user_id.
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # User A tries to delete (endpoint should only affect A, not accept user_id param)
        response = client.delete(
            '/api/auth/profile',
            json={'user_id': str(user_b_id)},  # Attempt to override target
            headers=get_auth_headers(user_a_id)
        )

        # Verify B wasn't deleted
        user_b = db_session.get(User, user_b_id)
        assert user_b is not None, \
            "SECURITY VULNERABILITY: User B was deleted by User A's request"
