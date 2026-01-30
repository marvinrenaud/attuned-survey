"""
Security Vulnerability Fix Tests

These tests verify that the security vulnerabilities identified in the security scan
have been properly fixed. Each fix must have:
1. 401 test (request without auth token)
2. 403 test (request with wrong user's token / insufficient permissions)
3. Success test (authorized access)

CRITICAL: All these tests MUST pass. Failures indicate security vulnerabilities.
"""

import pytest
import jwt
import uuid
import os
from unittest.mock import patch
from datetime import datetime, timedelta

from backend.src.models.user import User
from backend.src.models.profile import Profile
from backend.src.models.survey import SurveySubmission
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
    """Create two separate users for security testing."""
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    user_a = User(
        id=user_a_id,
        email="user_a@sectest.com",
        display_name="User A",
        subscription_tier='free',
        daily_activity_count=5,
        daily_activity_reset_at=datetime.utcnow()
    )
    user_b = User(
        id=user_b_id,
        email="user_b@sectest.com",
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
# FIX 1: sync_user.py - Internal Webhook Auth
# =============================================================================

class TestSyncUserAuth:
    """Tests for Fix 1: /api/users/<user_id>/sync requires internal webhook auth."""

    def test_sync_user_unauthorized_no_token(self, client, db_session, two_users):
        """401: Request without any authorization."""
        response = client.post(f'/api/users/{two_users["user_a_id"]}/sync')
        assert response.status_code == 401, \
            f"SECURITY VULNERABILITY: sync_user accessible without auth. Got {response.status_code}"

    def test_sync_user_unauthorized_invalid_secret(self, client, db_session, two_users):
        """401: Request with invalid internal secret."""
        with patch.dict(os.environ, {"INTERNAL_WEBHOOK_SECRET": "correct-secret"}):
            response = client.post(
                f'/api/users/{two_users["user_a_id"]}/sync',
                headers={'Authorization': 'Bearer wrong-secret'}
            )
            assert response.status_code == 401, \
                f"SECURITY VULNERABILITY: sync_user accepts invalid secret. Got {response.status_code}"

    def test_sync_user_success_with_valid_secret(self, client, db_session, two_users):
        """Success: Request with valid internal webhook secret."""
        with patch.dict(os.environ, {"INTERNAL_WEBHOOK_SECRET": "correct-secret"}):
            response = client.post(
                f'/api/users/{two_users["user_a_id"]}/sync',
                headers={'Authorization': 'Bearer correct-secret'}
            )
            assert response.status_code == 200, \
                f"sync_user should succeed with valid secret. Got {response.status_code}"


# =============================================================================
# FIX 2: process_submission.py - Internal Webhook Auth
# =============================================================================

class TestProcessSubmissionAuth:
    """Tests for Fix 2: /api/survey/submissions/<id>/process requires internal webhook auth."""

    def test_process_submission_unauthorized_no_token(self, client, db_session):
        """401: Request without any authorization."""
        response = client.post('/api/survey/submissions/test-123/process')
        assert response.status_code == 401, \
            f"SECURITY VULNERABILITY: process_submission accessible without auth. Got {response.status_code}"

    def test_process_submission_unauthorized_invalid_secret(self, client, db_session):
        """401: Request with invalid internal secret."""
        with patch.dict(os.environ, {"INTERNAL_WEBHOOK_SECRET": "correct-secret"}):
            response = client.post(
                '/api/survey/submissions/test-123/process',
                headers={'Authorization': 'Bearer wrong-secret'}
            )
            assert response.status_code == 401, \
                f"SECURITY VULNERABILITY: process_submission accepts invalid secret. Got {response.status_code}"


# =============================================================================
# FIX 3: survey.py POST /submissions - Requires Auth
# =============================================================================

class TestCreateSubmissionAuth:
    """Tests for Fix 3: POST /api/survey/submissions requires authentication."""

    def test_create_submission_unauthorized(self, client, db_session):
        """401: Request without auth token."""
        response = client.post(
            '/api/survey/submissions',
            json={'name': 'Test', 'answers': {}}
        )
        assert response.status_code == 401, \
            f"SECURITY VULNERABILITY: create_submission accessible without auth. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_create_submission_success_with_auth(self, client, db_session, two_users):
        """Success: Authenticated user can create submission."""
        user_id = two_users['user_a_id']
        response = client.post(
            '/api/survey/submissions',
            json={'name': 'Test User', 'answers': {}},
            headers=get_auth_headers(user_id)
        )
        assert response.status_code == 201, \
            f"Authenticated user should be able to create submission. Got {response.status_code}"


# =============================================================================
# FIX 4: survey.py GET /submissions - Returns Only User's Data
# =============================================================================

class TestGetSubmissionsScoping:
    """Tests for Fix 4: GET /api/survey/submissions returns only authenticated user's data."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_get_submissions_only_own_data(self, client, db_session, two_users):
        """User should only see their own submissions, not other users'."""
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # Create submission for User A
        sub_a = SurveySubmission(
            submission_id=f'sub_a_{uuid.uuid4()}',
            user_id=user_a_id,
            payload_json={'owner': 'A'}
        )
        # Create submission for User B
        sub_b = SurveySubmission(
            submission_id=f'sub_b_{uuid.uuid4()}',
            user_id=user_b_id,
            payload_json={'owner': 'B'}
        )
        db_session.add_all([sub_a, sub_b])
        db_session.commit()

        # User A requests submissions
        response = client.get(
            '/api/survey/submissions',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 200
        data = response.json
        submissions = data.get('submissions', [])

        # User A should only see their own submission
        for sub in submissions:
            assert sub.get('owner') != 'B', \
                "SECURITY VULNERABILITY: User A can see User B's submission"


# =============================================================================
# FIX 8: survey.py GET /submissions/<id> - Ownership Check
# =============================================================================

class TestGetSubmissionIDOR:
    """Tests for Fix 8: GET /api/survey/submissions/<id> requires ownership."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_get_submission_forbidden_other_user(self, client, db_session, two_users):
        """403: User A cannot access User B's submission."""
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # Create submission for User B
        sub_b = SurveySubmission(
            submission_id=f'sub_b_private_{uuid.uuid4()}',
            user_id=user_b_id,
            payload_json={'secret': 'data'}
        )
        db_session.add(sub_b)
        db_session.commit()

        # User A tries to access User B's submission
        response = client.get(
            f'/api/survey/submissions/{sub_b.submission_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"SECURITY VULNERABILITY: User can access another user's submission. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_get_submission_success_own_data(self, client, db_session, two_users):
        """Success: User can access their own submission."""
        user_a_id = two_users['user_a_id']

        # Create submission for User A
        sub_a = SurveySubmission(
            submission_id=f'sub_a_own_{uuid.uuid4()}',
            user_id=user_a_id,
            payload_json={'my': 'data'}
        )
        db_session.add(sub_a)
        db_session.commit()

        # User A accesses their own submission
        response = client.get(
            f'/api/survey/submissions/{sub_a.submission_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 200, \
            f"User should be able to access their own submission. Got {response.status_code}"


# =============================================================================
# FIX 9: survey.py GET /compatibility - Authorization Check
# =============================================================================

class TestCompatibilityAuth:
    """Tests for Fix 9: /api/survey/compatibility requires user to own at least one submission."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_compatibility_forbidden_unrelated_submissions(self, client, db_session, two_users):
        """403: User cannot compute compatibility for submissions they don't own."""
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']
        user_c_id = uuid.uuid4()

        # Create User C
        user_c = User(id=user_c_id, email="user_c@sectest.com")
        db_session.add(user_c)

        # Create submissions for User B and User C (not User A)
        sub_b = SurveySubmission(
            submission_id=f'sub_b_compat_{uuid.uuid4()}',
            user_id=user_b_id,
            payload_json={'derived': {'power_dynamic': {}}}
        )
        sub_c = SurveySubmission(
            submission_id=f'sub_c_compat_{uuid.uuid4()}',
            user_id=user_c_id,
            payload_json={'derived': {'power_dynamic': {}}}
        )
        db_session.add_all([sub_b, sub_c])
        db_session.commit()

        # User A tries to compute compatibility between B and C
        response = client.get(
            f'/api/survey/compatibility/{sub_b.submission_id}/{sub_c.submission_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"SECURITY VULNERABILITY: User can compute compatibility for unrelated submissions. Got {response.status_code}"


# =============================================================================
# FIX 10: survey.py GET /export - Only User's Data
# =============================================================================

class TestExportScoping:
    """Tests for Fix 10: GET /api/survey/export returns only authenticated user's data."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_export_only_own_data(self, client, db_session, two_users):
        """Export should only include user's own submissions."""
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # Create submission for User A
        sub_a = SurveySubmission(
            submission_id=f'sub_a_export_{uuid.uuid4()}',
            user_id=user_a_id,
            payload_json={'owner': 'A'}
        )
        # Create submission for User B
        sub_b = SurveySubmission(
            submission_id=f'sub_b_export_{uuid.uuid4()}',
            user_id=user_b_id,
            payload_json={'owner': 'B'}
        )
        db_session.add_all([sub_a, sub_b])
        db_session.commit()

        # User A exports data
        response = client.get(
            '/api/survey/export',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 200
        data = response.json
        submissions = data.get('submissions', [])

        # User A should only see their own submission in export
        for sub in submissions:
            assert sub.get('owner') != 'B', \
                "SECURITY VULNERABILITY: User A's export contains User B's data"


# =============================================================================
# FIX 6: profile_sharing.py - Partner Connection Verification
# =============================================================================

class TestPartnerProfileIDOR:
    """Tests for Fix 6: /api/profile-sharing/partner-profile requires partner connection."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_partner_profile_forbidden_no_connection(self, client, db_session, two_users):
        """403: Cannot access profile of non-partner."""
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # Create profile for User B
        profile_b = Profile(
            submission_id=f'profile_b_{uuid.uuid4()}',
            user_id=user_b_id,
            profile_version='0.4',
            power_dynamic={},
            arousal_propensity={},
            domain_scores={},
            activities={},
            truth_topics={},
            boundaries={},
            anatomy={'anatomy_self': ['penis'], 'anatomy_preference': ['vagina']}
        )
        db_session.add(profile_b)
        db_session.commit()

        # User A (not connected to B) tries to access B's profile
        response = client.get(
            f'/api/profile-sharing/partner-profile/{user_b_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"SECURITY VULNERABILITY: User can access non-partner's profile. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_partner_profile_success_with_connection(self, client, db_session, two_users):
        """Success: Can access profile of connected partner."""
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # Create accepted partner connection
        connection = PartnerConnection(
            requester_user_id=user_a_id,
            recipient_user_id=user_b_id,
            recipient_email="user_b@sectest.com",
            status='accepted',
            connection_token=str(uuid.uuid4()),
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        db_session.add(connection)

        # Create profile for User B
        profile_b = Profile(
            submission_id=f'profile_b_connected_{uuid.uuid4()}',
            user_id=user_b_id,
            profile_version='0.4',
            power_dynamic={},
            arousal_propensity={},
            domain_scores={},
            activities={},
            truth_topics={},
            boundaries={},
            anatomy={'anatomy_self': ['penis'], 'anatomy_preference': ['vagina']}
        )
        db_session.add(profile_b)
        db_session.commit()

        # User A (connected to B) accesses B's profile
        response = client.get(
            f'/api/profile-sharing/partner-profile/{user_b_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 200, \
            f"Connected partner should be able to access profile. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_partner_profile_success_with_remembered_partner(self, client, db_session, two_users):
        """Success: Can access profile of remembered partner."""
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # Create remembered partner relationship
        remembered = RememberedPartner(
            user_id=user_a_id,
            partner_user_id=user_b_id,
            partner_name="User B",
            partner_email="user_b@sectest.com"
        )
        db_session.add(remembered)

        # Create profile for User B
        profile_b = Profile(
            submission_id=f'profile_b_remembered_{uuid.uuid4()}',
            user_id=user_b_id,
            profile_version='0.4',
            power_dynamic={},
            arousal_propensity={},
            domain_scores={},
            activities={},
            truth_topics={},
            boundaries={},
            anatomy={'anatomy_self': ['penis'], 'anatomy_preference': ['vagina']}
        )
        db_session.add(profile_b)
        db_session.commit()

        # User A (has B as remembered partner) accesses B's profile
        response = client.get(
            f'/api/profile-sharing/partner-profile/{user_b_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 200, \
            f"Should be able to access remembered partner's profile. Got {response.status_code}"


# =============================================================================
# FIX 7: system_admin.py - Admin Role Check
# =============================================================================

class TestSystemAdminAuth:
    """Tests for Fix 7: /api/system-admin/cache/refresh requires admin role."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key", "ADMIN_USER_IDS": ""})
    def test_cache_refresh_forbidden_non_admin(self, client, db_session, two_users):
        """403: Non-admin user cannot refresh cache."""
        response = client.post(
            '/api/system-admin/cache/refresh',
            headers=get_auth_headers(two_users['user_a_id'])
        )

        assert response.status_code == 403, \
            f"SECURITY VULNERABILITY: Non-admin can refresh cache. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_cache_refresh_success_admin(self, client, db_session, two_users):
        """Success: Admin user can refresh cache."""
        admin_id = str(two_users['user_a_id'])

        with patch.dict(os.environ, {"ADMIN_USER_IDS": admin_id}):
            response = client.post(
                '/api/system-admin/cache/refresh',
                headers=get_auth_headers(admin_id)
            )

            assert response.status_code == 200, \
                f"Admin should be able to refresh cache. Got {response.status_code}"

    def test_cache_refresh_unauthorized_no_token(self, client, db_session):
        """401: Request without auth token."""
        response = client.post('/api/system-admin/cache/refresh')

        assert response.status_code == 401, \
            f"SECURITY VULNERABILITY: Cache refresh accessible without auth. Got {response.status_code}"
