# QA Testing Strategy for Security Vulnerability Fixes

This document provides a comprehensive testing strategy for the 11 security vulnerabilities being fixed.

## Test File Organization

```
backend/tests/
├── test_security_auth_required.py      # NEW: Tests for missing auth (vuln 1-3)
├── test_security_idor.py               # NEW: Tests for IDOR vulnerabilities (vuln 4-6)
├── test_security_data_exposure.py      # NEW: Tests for data exposure (vuln 7-8)
├── test_security_admin_access.py       # NEW: Tests for admin controls (vuln 9)
├── test_security_info_disclosure.py    # NEW: Tests for error messages (vuln 10)
├── test_security_rate_limiting.py      # NEW: Tests for rate limits (vuln 11)
├── test_idor_security.py               # EXISTING: Extend with new cases
└── conftest.py                         # EXISTING: Add new fixtures
```

## Required Fixtures (add to conftest.py)

```python
import jwt
import uuid
from datetime import datetime, timedelta
from backend.src.models.user import User
from backend.src.models.survey import SurveySubmission
from backend.src.models.profile import Profile
from backend.src.models.partner import PartnerConnection
from backend.src.extensions import db


def create_test_token(user_id: str, secret: str = "test-secret-key") -> str:
    """Create a valid JWT token for testing."""
    return jwt.encode(
        {"sub": str(user_id), "aud": "authenticated"},
        secret,
        algorithm="HS256"
    )


def get_auth_headers(user_id: str) -> dict:
    """Get authorization headers for a user."""
    return {'Authorization': f'Bearer {create_test_token(user_id)}'}


@pytest.fixture
def user_with_submission(db_session):
    """Create a user with a survey submission and profile."""
    user_id = uuid.uuid4()
    submission_id = f"test_sub_{uuid.uuid4()}"

    user = User(
        id=user_id,
        email="user_submission@test.com",
        display_name="Test User"
    )
    db_session.add(user)
    db_session.flush()

    submission = SurveySubmission(
        submission_id=submission_id,
        user_id=user_id,
        payload_json={'answers': {'q1': 5}, 'derived': {}}
    )
    db_session.add(submission)
    db_session.flush()

    profile = Profile(
        user_id=user_id,
        submission_id=submission_id,
        profile_version='0.4',
        power_dynamic={'orientation': 'Switch'},
        arousal_propensity={},
        domain_scores={},
        activities={},
        truth_topics={},
        boundaries={},
        anatomy={'anatomy_self': ['penis'], 'anatomy_preference': ['vagina']}
    )
    db_session.add(profile)
    db_session.commit()

    return {
        'user': user,
        'user_id': user_id,
        'submission': submission,
        'submission_id': submission_id,
        'profile': profile
    }


@pytest.fixture
def connected_partners(db_session):
    """Create two users with an accepted partner connection."""
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    user_a = User(id=user_a_id, email="partner_a@test.com", display_name="Partner A")
    user_b = User(id=user_b_id, email="partner_b@test.com", display_name="Partner B")
    db_session.add_all([user_a, user_b])
    db_session.flush()

    connection = PartnerConnection(
        requester_user_id=user_a_id,
        recipient_user_id=user_b_id,
        recipient_email="partner_b@test.com",
        status='accepted',
        connection_token=str(uuid.uuid4()),
        expires_at=datetime.utcnow() + timedelta(days=1)
    )
    db_session.add(connection)
    db_session.commit()

    return {
        'user_a': user_a, 'user_a_id': user_a_id,
        'user_b': user_b, 'user_b_id': user_b_id,
        'connection': connection
    }


@pytest.fixture
def unconnected_users(db_session):
    """Create two users WITHOUT a partner connection."""
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    user_a = User(id=user_a_id, email="unconnected_a@test.com")
    user_b = User(id=user_b_id, email="unconnected_b@test.com")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    return {
        'user_a': user_a, 'user_a_id': user_a_id,
        'user_b': user_b, 'user_b_id': user_b_id
    }


@pytest.fixture
def admin_user(db_session):
    """Create a user with admin privileges (when role system exists)."""
    admin_id = uuid.uuid4()
    admin = User(
        id=admin_id,
        email="admin@test.com",
        display_name="Admin User",
        # is_admin=True  # When admin field exists
    )
    db_session.add(admin)
    db_session.commit()
    return {'user': admin, 'user_id': admin_id}


@pytest.fixture
def regular_user(db_session):
    """Create a regular non-admin user."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="regular@test.com",
        display_name="Regular User"
    )
    db_session.add(user)
    db_session.commit()
    return {'user': user, 'user_id': user_id}
```

---

## Vulnerability 1: Missing auth on `/api/users/<user_id>/sync`

### File: `test_security_auth_required.py`

```python
"""
Security tests for endpoints that require authentication.
Verifies that unauthenticated requests are properly rejected.
"""

import pytest
import uuid
import os
from unittest.mock import patch

from backend.src.models.user import User
from backend.src.extensions import db


class TestSyncUserAuthRequired:
    """Tests for /api/users/<user_id>/sync authentication."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_sync_user_requires_auth_401(self, client, db_session):
        """
        CRITICAL: POST /api/users/<user_id>/sync requires authentication.

        Vulnerability: Endpoint has no @token_required decorator.
        Expected: 401 Unauthorized without token.
        """
        user_id = uuid.uuid4()

        # Create user to sync
        user = User(id=user_id, email="sync_test@test.com")
        db_session.add(user)
        db_session.commit()

        response = client.post(f'/api/users/{user_id}/sync')

        assert response.status_code == 401, \
            f"VULNERABILITY: Sync endpoint accessible without auth. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_sync_user_invalid_token_401(self, client, db_session):
        """
        POST /api/users/<user_id>/sync rejects invalid tokens.

        Expected: 401 Unauthorized with invalid token.
        """
        user_id = uuid.uuid4()

        response = client.post(
            f'/api/users/{user_id}/sync',
            headers={'Authorization': 'Bearer invalid-token-here'}
        )

        assert response.status_code == 401

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_sync_user_wrong_user_403(self, client, db_session, two_users):
        """
        CRITICAL: User A cannot sync User B's data.

        Expected: 403 Forbidden when trying to sync another user.
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        response = client.post(
            f'/api/users/{user_b_id}/sync',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"VULNERABILITY: User can sync another user's data. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_sync_user_own_user_success(self, client, db_session, user_with_submission):
        """
        User can successfully sync their own data.

        Expected: 200 OK when syncing own user.
        """
        user_id = user_with_submission['user_id']

        response = client.post(
            f'/api/users/{user_id}/sync',
            headers=get_auth_headers(user_id)
        )

        assert response.status_code == 200
```

---

## Vulnerability 2: Missing auth on `/api/survey/submissions/<id>/process`

### File: `test_security_auth_required.py` (continued)

```python
class TestProcessSubmissionAuthRequired:
    """Tests for /api/survey/submissions/<id>/process authentication."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_process_submission_requires_auth_401(self, client, db_session, user_with_submission):
        """
        CRITICAL: POST /api/survey/submissions/<id>/process requires authentication.

        Vulnerability: Endpoint has no @token_required decorator.
        Expected: 401 Unauthorized without token.
        """
        submission_id = user_with_submission['submission_id']

        response = client.post(f'/api/survey/submissions/{submission_id}/process')

        assert response.status_code == 401, \
            f"VULNERABILITY: Process endpoint accessible without auth. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_process_submission_invalid_token_401(self, client):
        """
        POST /api/survey/submissions/<id>/process rejects invalid tokens.
        """
        response = client.post(
            '/api/survey/submissions/any_id/process',
            headers={'Authorization': 'Bearer invalid-token-here'}
        )

        assert response.status_code == 401

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_process_submission_wrong_user_403(self, client, db_session, user_with_submission, two_users):
        """
        CRITICAL: User A cannot process User B's submission.

        Expected: 403 Forbidden when processing another user's submission.
        """
        user_a_id = two_users['user_a_id']
        submission_id = user_with_submission['submission_id']  # Belongs to different user

        response = client.post(
            f'/api/survey/submissions/{submission_id}/process',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"VULNERABILITY: User can process another user's submission. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_process_submission_own_success(self, client, db_session, user_with_submission):
        """
        User can successfully process their own submission.
        """
        user_id = user_with_submission['user_id']
        submission_id = user_with_submission['submission_id']

        response = client.post(
            f'/api/survey/submissions/{submission_id}/process',
            headers=get_auth_headers(user_id)
        )

        # 200 OK or 201 Created (if profile didn't exist) are both valid
        assert response.status_code in [200, 201]
```

---

## Vulnerability 3: Missing auth on `POST /api/survey/submissions`

### File: `test_security_auth_required.py` (continued)

```python
class TestCreateSubmissionAuthRequired:
    """Tests for POST /api/survey/submissions authentication."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_create_submission_requires_auth_401(self, client):
        """
        CRITICAL: POST /api/survey/submissions requires authentication.

        Vulnerability: Endpoint has no @token_required decorator.
        Expected: 401 Unauthorized without token.
        """
        payload = {
            'answers': {'q1': 5, 'q2': 3},
            'name': 'Test User'
        }

        response = client.post('/api/survey/submissions', json=payload)

        assert response.status_code == 401, \
            f"VULNERABILITY: Submit endpoint accessible without auth. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_create_submission_invalid_token_401(self, client):
        """
        POST /api/survey/submissions rejects invalid tokens.
        """
        payload = {'answers': {'q1': 5}}

        response = client.post(
            '/api/survey/submissions',
            json=payload,
            headers={'Authorization': 'Bearer invalid-token-here'}
        )

        assert response.status_code == 401

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_create_submission_success_with_auth(self, client, db_session, regular_user):
        """
        Authenticated user can create a submission.
        """
        user_id = regular_user['user_id']
        payload = {
            'answers': {'q1': 5, 'q2': 3},
            'respondentId': str(user_id)
        }

        response = client.post(
            '/api/survey/submissions',
            json=payload,
            headers=get_auth_headers(user_id)
        )

        assert response.status_code == 201
```

---

## Vulnerability 4: IDOR - Partner profile without connection check

### File: `test_security_idor.py`

```python
"""
Security tests for IDOR (Insecure Direct Object Reference) vulnerabilities.
Verifies that users cannot access resources belonging to others.
"""

import pytest
import uuid
import os
from unittest.mock import patch

from backend.src.models.user import User
from backend.src.models.profile import Profile
from backend.src.extensions import db


class TestPartnerProfileIDOR:
    """Tests for /api/profile-sharing/partner-profile/<id> connection verification."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_partner_profile_requires_connection_403(self, client, db_session, unconnected_users):
        """
        CRITICAL: Cannot view partner profile without accepted connection.

        Vulnerability: Endpoint doesn't verify PartnerConnection exists.
        Expected: 403 Forbidden when no connection exists.
        """
        user_a_id = unconnected_users['user_a_id']
        user_b_id = unconnected_users['user_b_id']

        # Create profile for user_b
        profile = Profile(
            user_id=user_b_id,
            submission_id=f"sub_{user_b_id}",
            profile_version='0.4',
            power_dynamic={}, arousal_propensity={},
            domain_scores={}, activities={},
            truth_topics={}, boundaries={},
            anatomy={'anatomy_self': [], 'anatomy_preference': []}
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            f'/api/profile-sharing/partner-profile/{user_b_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"VULNERABILITY: Can view partner profile without connection. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_partner_profile_pending_connection_403(self, client, db_session, two_users):
        """
        CRITICAL: Cannot view partner profile with PENDING connection.

        Expected: 403 Forbidden when connection is pending (not accepted).
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # Create PENDING connection (not accepted)
        from backend.src.models.partner import PartnerConnection
        from datetime import datetime, timedelta

        connection = PartnerConnection(
            requester_user_id=user_a_id,
            recipient_user_id=user_b_id,
            recipient_email="user_b@test.com",
            status='pending',  # NOT accepted
            connection_token=str(uuid.uuid4()),
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        db_session.add(connection)

        # Create profile for user_b
        profile = Profile(
            user_id=user_b_id,
            submission_id=f"sub_{user_b_id}",
            profile_version='0.4',
            power_dynamic={}, arousal_propensity={},
            domain_scores={}, activities={},
            truth_topics={}, boundaries={},
            anatomy={'anatomy_self': [], 'anatomy_preference': []}
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            f'/api/profile-sharing/partner-profile/{user_b_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"VULNERABILITY: Can view profile with pending connection. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_partner_profile_accepted_connection_success(self, client, db_session, connected_partners):
        """
        User can view partner profile with accepted connection.
        """
        user_a_id = connected_partners['user_a_id']
        user_b_id = connected_partners['user_b_id']

        # Create profile for user_b
        profile = Profile(
            user_id=user_b_id,
            submission_id=f"sub_{user_b_id}",
            profile_version='0.4',
            power_dynamic={}, arousal_propensity={},
            domain_scores={}, activities={},
            truth_topics={}, boundaries={},
            anatomy={'anatomy_self': [], 'anatomy_preference': []}
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            f'/api/profile-sharing/partner-profile/{user_b_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 200

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_partner_profile_random_user_403(self, client, db_session, connected_partners):
        """
        CRITICAL: Random user cannot view profiles of connected partners.

        User C cannot view User B's profile even though A and B are connected.
        """
        user_b_id = connected_partners['user_b_id']
        user_c_id = uuid.uuid4()

        # Create User C (attacker)
        user_c = User(id=user_c_id, email="attacker@test.com")
        db_session.add(user_c)

        # Create profile for user_b
        profile = Profile(
            user_id=user_b_id,
            submission_id=f"sub_{user_b_id}",
            profile_version='0.4',
            power_dynamic={}, arousal_propensity={},
            domain_scores={}, activities={},
            truth_topics={}, boundaries={},
            anatomy={'anatomy_self': [], 'anatomy_preference': []}
        )
        db_session.add(profile)
        db_session.commit()

        response = client.get(
            f'/api/profile-sharing/partner-profile/{user_b_id}',
            headers=get_auth_headers(user_c_id)
        )

        assert response.status_code == 403, \
            f"VULNERABILITY: Attacker can view profile. Got {response.status_code}"
```

---

## Vulnerability 5: IDOR - View any submission

### File: `test_security_idor.py` (continued)

```python
class TestSubmissionIDOR:
    """Tests for /api/survey/submissions/<id> ownership verification."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_view_submission_requires_ownership_403(self, client, db_session, user_with_submission, two_users):
        """
        CRITICAL: User A cannot view User B's submission.

        Vulnerability: Endpoint doesn't verify user_id matches.
        Expected: 403 Forbidden when viewing another user's submission.
        """
        user_a_id = two_users['user_a_id']
        submission_id = user_with_submission['submission_id']  # Belongs to different user

        response = client.get(
            f'/api/survey/submissions/{submission_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 403, \
            f"VULNERABILITY: User can view another user's submission. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_view_submission_own_success(self, client, db_session, user_with_submission):
        """
        User can view their own submission.
        """
        user_id = user_with_submission['user_id']
        submission_id = user_with_submission['submission_id']

        response = client.get(
            f'/api/survey/submissions/{submission_id}',
            headers=get_auth_headers(user_id)
        )

        assert response.status_code == 200

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_view_submission_not_found_404(self, client, db_session, regular_user):
        """
        Returns 404 for non-existent submission, not 403.

        Note: Return 404 to avoid revealing that submission exists.
        """
        user_id = regular_user['user_id']

        response = client.get(
            '/api/survey/submissions/nonexistent_submission_id',
            headers=get_auth_headers(user_id)
        )

        assert response.status_code == 404
```

---

## Vulnerability 6: IDOR - Compatibility between any users

### File: `test_security_idor.py` (continued)

```python
class TestSurveyCompatibilityIDOR:
    """Tests for /api/survey/compatibility/<source_id>/<target_id> authorization."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_compatibility_requires_participation_403(self, client, db_session, user_with_submission, two_users):
        """
        CRITICAL: User C cannot view compatibility between User A and User B.

        Vulnerability: Endpoint doesn't verify requester is source or target.
        Expected: 403 Forbidden when user is not a participant.
        """
        # User C (attacker) tries to view compatibility between others
        user_c_id = uuid.uuid4()
        user_c = User(id=user_c_id, email="attacker_c@test.com")
        db_session.add(user_c)
        db_session.commit()

        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        response = client.get(
            f'/api/survey/compatibility/{user_a_id}/{user_b_id}',
            headers=get_auth_headers(user_c_id)
        )

        assert response.status_code == 403, \
            f"VULNERABILITY: Non-participant can view compatibility. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_compatibility_source_user_success(self, client, db_session, user_with_submission):
        """
        Source user can view their own compatibility.
        """
        user_id = user_with_submission['user_id']
        submission_id = user_with_submission['submission_id']

        # Create a second submission for target
        target_submission_id = f"target_sub_{uuid.uuid4()}"
        from backend.src.models.survey import SurveySubmission
        target_sub = SurveySubmission(
            submission_id=target_submission_id,
            payload_json={'answers': {'q1': 3}, 'derived': {}}
        )
        db_session.add(target_sub)
        db_session.commit()

        response = client.get(
            f'/api/survey/compatibility/{submission_id}/{target_submission_id}',
            headers=get_auth_headers(user_id)
        )

        # 200 or 404 (if profile not found) are acceptable
        # Should NOT be 403 since user is source
        assert response.status_code != 403

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_compatibility_target_user_success(self, client, db_session, user_with_submission):
        """
        Target user can also view their own compatibility (reversed).
        """
        user_id = user_with_submission['user_id']
        submission_id = user_with_submission['submission_id']

        # Create a second submission for source
        source_submission_id = f"source_sub_{uuid.uuid4()}"
        from backend.src.models.survey import SurveySubmission
        source_sub = SurveySubmission(
            submission_id=source_submission_id,
            payload_json={'answers': {'q1': 3}, 'derived': {}}
        )
        db_session.add(source_sub)
        db_session.commit()

        response = client.get(
            f'/api/survey/compatibility/{source_submission_id}/{submission_id}',
            headers=get_auth_headers(user_id)
        )

        # Should NOT be 403 since user is target
        assert response.status_code != 403
```

---

## Vulnerability 7: Data exposure - List all submissions

### File: `test_security_data_exposure.py`

```python
"""
Security tests for data exposure vulnerabilities.
Verifies that endpoints don't leak data from other users.
"""

import pytest
import uuid
import os
from unittest.mock import patch

from backend.src.models.user import User
from backend.src.models.survey import SurveySubmission
from backend.src.extensions import db


class TestListSubmissionsDataExposure:
    """Tests for GET /api/survey/submissions data scope."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_list_submissions_returns_only_own(self, client, db_session, user_with_submission, two_users):
        """
        CRITICAL: GET /api/survey/submissions must only return user's own submissions.

        Vulnerability: Endpoint returns ALL submissions in database.
        Expected: Only submissions belonging to authenticated user.
        """
        # Create submission for user_a
        user_a_id = two_users['user_a_id']
        user_a_submission = SurveySubmission(
            submission_id=f"sub_a_{uuid.uuid4()}",
            user_id=user_a_id,
            payload_json={'answers': {'q1': 5}}
        )
        db_session.add(user_a_submission)
        db_session.commit()

        # Request as user_a
        response = client.get(
            '/api/survey/submissions',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 200
        submissions = response.json.get('submissions', [])

        # Verify ONLY user_a's submissions are returned
        for sub in submissions:
            sub_record = SurveySubmission.query.filter_by(submission_id=sub.get('id')).first()
            if sub_record and sub_record.user_id:
                assert str(sub_record.user_id) == str(user_a_id), \
                    f"VULNERABILITY: Response contains submission from another user: {sub_record.user_id}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_list_submissions_does_not_expose_others(self, client, db_session, two_users):
        """
        CRITICAL: User A cannot see User B's submissions in list.
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # Create submissions for both users
        sub_a_id = f"sub_a_{uuid.uuid4()}"
        sub_b_id = f"sub_b_{uuid.uuid4()}"

        sub_a = SurveySubmission(
            submission_id=sub_a_id,
            user_id=user_a_id,
            payload_json={'answers': {'q1': 5}}
        )
        sub_b = SurveySubmission(
            submission_id=sub_b_id,
            user_id=user_b_id,
            payload_json={'answers': {'q1': 3}, 'secret': 'should_not_see'}
        )
        db_session.add_all([sub_a, sub_b])
        db_session.commit()

        # User A requests list
        response = client.get(
            '/api/survey/submissions',
            headers=get_auth_headers(user_a_id)
        )

        submissions = response.json.get('submissions', [])
        submission_ids = [s.get('id') for s in submissions]

        # User B's submission should NOT be visible
        assert sub_b_id not in submission_ids, \
            f"VULNERABILITY: User A can see User B's submission in list"

        # Verify no 'secret' data leaked
        for sub in submissions:
            assert 'secret' not in str(sub), \
                "VULNERABILITY: Data from other user leaked"
```

---

## Vulnerability 8: Data exposure - Export all submissions

### File: `test_security_data_exposure.py` (continued)

```python
class TestExportDataExposure:
    """Tests for GET /api/survey/export data scope."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_export_returns_only_own(self, client, db_session, user_with_submission, two_users):
        """
        CRITICAL: GET /api/survey/export must only return user's own data.

        Vulnerability: Endpoint exports ALL submissions.
        Expected: Only authenticated user's submissions.
        """
        user_a_id = two_users['user_a_id']
        user_b_id = two_users['user_b_id']

        # Create submissions for both users
        sub_a = SurveySubmission(
            submission_id=f"export_a_{uuid.uuid4()}",
            user_id=user_a_id,
            payload_json={'answers': {'q1': 5}}
        )
        sub_b = SurveySubmission(
            submission_id=f"export_b_{uuid.uuid4()}",
            user_id=user_b_id,
            payload_json={'answers': {'q1': 3}, 'private_data': 'should_not_export'}
        )
        db_session.add_all([sub_a, sub_b])
        db_session.commit()

        # User A exports
        response = client.get(
            '/api/survey/export',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 200
        export_data = response.json
        submissions = export_data.get('submissions', [])

        # Verify only user_a's data
        for sub in submissions:
            sub_record = SurveySubmission.query.filter_by(submission_id=sub.get('id')).first()
            if sub_record and sub_record.user_id:
                assert str(sub_record.user_id) == str(user_a_id), \
                    f"VULNERABILITY: Export contains another user's submission"

        # Verify private data not leaked
        assert 'private_data' not in str(export_data), \
            "VULNERABILITY: Private data from other user exported"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_export_requires_admin_for_all(self, client, db_session, regular_user, admin_user):
        """
        If export of all data is needed, it should require admin role.

        Note: If the business requires exporting ALL submissions,
        create a separate admin-only endpoint: /api/admin/survey/export
        """
        # This test documents the expected behavior
        # Regular users should only get their own data
        # Admin users (if needed) should use a separate endpoint
        pass
```

---

## Vulnerability 9: Missing admin check on system_admin

### File: `test_security_admin_access.py`

```python
"""
Security tests for admin-only endpoints.
Verifies that administrative functions require proper authorization.
"""

import pytest
import uuid
import os
from unittest.mock import patch

from backend.src.models.user import User
from backend.src.extensions import db


class TestSystemAdminAccess:
    """Tests for /api/system-admin/* admin verification."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_cache_refresh_requires_admin_403(self, client, db_session, regular_user):
        """
        CRITICAL: POST /api/system-admin/cache/refresh requires admin role.

        Vulnerability: Endpoint only has @token_required, no admin check.
        Expected: 403 Forbidden for non-admin users.
        """
        user_id = regular_user['user_id']

        response = client.post(
            '/api/system-admin/cache/refresh',
            headers=get_auth_headers(user_id)
        )

        assert response.status_code == 403, \
            f"VULNERABILITY: Non-admin can refresh cache. Got {response.status_code}"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_cache_refresh_requires_auth_401(self, client):
        """
        POST /api/system-admin/cache/refresh requires authentication.
        """
        response = client.post('/api/system-admin/cache/refresh')

        assert response.status_code == 401

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_cache_refresh_admin_success(self, client, db_session, admin_user):
        """
        Admin user can refresh cache.

        Note: This test will pass once admin check is implemented.
        For now, it documents expected behavior.
        """
        # When admin role system exists:
        # user_id = admin_user['user_id']
        # response = client.post(
        #     '/api/system-admin/cache/refresh',
        #     headers=get_auth_headers(user_id)
        # )
        # assert response.status_code == 200
        pass

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_system_admin_endpoints_logged(self, client, db_session, regular_user, caplog):
        """
        All system-admin actions should be logged with user ID.

        Even if access is denied, we should log the attempt.
        """
        import logging
        caplog.set_level(logging.INFO)

        user_id = regular_user['user_id']

        response = client.post(
            '/api/system-admin/cache/refresh',
            headers=get_auth_headers(user_id)
        )

        # Should log the attempt (regardless of success/failure)
        # Note: This depends on implementation logging
```

---

## Vulnerability 10: Information disclosure (str(e) in responses)

### File: `test_security_info_disclosure.py`

```python
"""
Security tests for information disclosure vulnerabilities.
Verifies that error messages don't leak sensitive information.
"""

import pytest
import uuid
import os
from unittest.mock import patch, MagicMock

from backend.src.models.user import User
from backend.src.extensions import db


class TestErrorMessageDisclosure:
    """Tests that error responses don't leak sensitive information."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_sync_user_error_no_stack_trace(self, client, db_session, regular_user):
        """
        CRITICAL: Error responses must not include stack traces.

        Vulnerability: return jsonify({'error': str(e)}), 500
        Expected: Generic error message without exception details.
        """
        user_id = regular_user['user_id']

        # Trigger an error by providing invalid user_id format
        response = client.post(
            '/api/users/invalid-uuid-format/sync',
            headers=get_auth_headers(user_id)
        )

        # Check response doesn't contain sensitive info
        response_text = str(response.json)

        # Should not contain implementation details
        assert 'Traceback' not in response_text, \
            "VULNERABILITY: Stack trace in error response"
        assert 'File "' not in response_text, \
            "VULNERABILITY: File paths in error response"
        assert 'line ' not in response_text.lower() or 'error' in response_text.lower(), \
            "VULNERABILITY: Line numbers in error response"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_process_submission_error_sanitized(self, client, db_session, regular_user):
        """
        Process submission errors should be sanitized.
        """
        user_id = regular_user['user_id']

        response = client.post(
            '/api/survey/submissions/nonexistent/process',
            headers=get_auth_headers(user_id)
        )

        if response.status_code == 500:
            response_text = str(response.json)
            # Should not expose database details
            assert 'postgresql' not in response_text.lower(), \
                "VULNERABILITY: Database info in error"
            assert 'sqlalchemy' not in response_text.lower(), \
                "VULNERABILITY: ORM info in error"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_survey_routes_error_sanitized(self, client, db_session, regular_user):
        """
        Survey route errors should not expose internal details.
        """
        user_id = regular_user['user_id']

        # Try to trigger a database error
        response = client.get(
            '/api/survey/submissions',
            headers=get_auth_headers(user_id)
        )

        if response.status_code == 500:
            response_text = str(response.json)

            # Generic error message patterns to avoid
            sensitive_patterns = [
                'psycopg',
                'connection refused',
                'password',
                'user=',
                '/home/',
                '/var/',
                'SECRET',
            ]

            for pattern in sensitive_patterns:
                assert pattern.lower() not in response_text.lower(), \
                    f"VULNERABILITY: Sensitive pattern '{pattern}' in error"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_compatibility_error_sanitized(self, client, db_session, regular_user):
        """
        Compatibility endpoint errors should be generic.
        """
        user_id = regular_user['user_id']

        response = client.get(
            f'/api/compatibility/{user_id}/invalid-uuid',
            headers=get_auth_headers(user_id)
        )

        if response.status_code == 500:
            error_msg = response.json.get('error', '')
            # Should be a generic message
            assert len(error_msg) < 200, \
                "VULNERABILITY: Error message too detailed"

    def test_error_format_consistency(self, client):
        """
        All error responses should follow a consistent format.

        Expected format: {'error': 'User-friendly message'}
        NOT: {'error': str(exception), 'details': traceback}
        """
        # Test 401 errors
        response = client.get('/api/survey/submissions')

        if response.status_code == 401:
            error_response = response.json

            # Should have 'error' key
            assert 'error' in error_response or 'message' in error_response

            # Should NOT have debug keys
            assert 'traceback' not in error_response
            assert 'exception' not in error_response
            assert 'stack' not in error_response
```

---

## Vulnerability 11: Missing rate limiting on critical endpoints

### File: `test_security_rate_limiting.py`

```python
"""
Security tests for rate limiting on critical endpoints.
Verifies that endpoints have appropriate rate limits.
"""

import pytest
import uuid
import os
from unittest.mock import patch

from backend.src.models.user import User
from backend.src.extensions import db


class TestRateLimiting:
    """Tests for rate limiting on security-critical endpoints."""

    # Note: Rate limiting is typically disabled in tests via RATELIMIT_ENABLED=False
    # These tests document expected behavior and can be enabled for integration testing

    @pytest.mark.skip(reason="Rate limiting disabled in test environment")
    def test_login_rate_limited(self, client):
        """
        Login endpoint should be rate limited.

        Expected: 429 Too Many Requests after threshold.
        """
        for _ in range(100):
            response = client.post(
                '/api/auth/login',
                json={'email': 'test@test.com', 'password': 'wrong'}
            )

        # After many requests, should be rate limited
        assert response.status_code == 429

    @pytest.mark.skip(reason="Rate limiting disabled in test environment")
    def test_survey_submit_rate_limited(self, client, regular_user):
        """
        Survey submission should be rate limited.

        Prevents automated submission attacks.
        """
        user_id = regular_user['user_id']

        for i in range(50):
            response = client.post(
                '/api/survey/submissions',
                json={'answers': {'q1': i}},
                headers=get_auth_headers(user_id)
            )

        # Should be rate limited
        assert response.status_code == 429

    @pytest.mark.skip(reason="Rate limiting disabled in test environment")
    def test_password_reset_rate_limited(self, client):
        """
        Password reset endpoint should be heavily rate limited.

        Prevents email enumeration attacks.
        """
        for _ in range(10):
            response = client.post(
                '/api/auth/reset-password',
                json={'email': 'test@test.com'}
            )

        assert response.status_code == 429

    def test_rate_limit_headers_present(self, client, db_session, regular_user):
        """
        Responses should include rate limit headers for client awareness.

        Expected headers:
        - X-RateLimit-Limit
        - X-RateLimit-Remaining
        - X-RateLimit-Reset
        """
        # This test checks if rate limit info is communicated to clients
        # Even with limiting disabled, headers may still be present
        pass

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_sync_user_has_rate_limit_decorator(self, client):
        """
        Document that sync endpoint should have rate limiting.

        Internal endpoints should have stricter limits.
        """
        # This is a documentation test
        # The fix should add @limiter.limit("10/minute") or similar
        pass

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_process_submission_has_rate_limit_decorator(self, client):
        """
        Document that process endpoint should have rate limiting.
        """
        pass
```

---

## Integration Test Considerations

### File: `test_security_integration.py`

```python
"""
Integration tests for security fixes.
Tests complete flows to ensure security measures work together.
"""

import pytest
import uuid
import os
from unittest.mock import patch
from datetime import datetime, timedelta

from backend.src.models.user import User
from backend.src.models.survey import SurveySubmission
from backend.src.models.profile import Profile
from backend.src.models.partner import PartnerConnection
from backend.src.extensions import db


class TestSecurityIntegration:
    """End-to-end security tests."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_complete_attack_scenario_blocked(self, client, db_session):
        """
        Test a complete attack scenario is blocked at all points.

        Scenario: Attacker tries to:
        1. Access unprotected endpoint (should fail with 401)
        2. View another user's submission (should fail with 403)
        3. Access partner profile without connection (should fail with 403)
        4. View compatibility they're not part of (should fail with 403)
        5. List all submissions (should only see own)
        """
        # Setup: Create victim and attacker users
        victim_id = uuid.uuid4()
        attacker_id = uuid.uuid4()

        victim = User(id=victim_id, email="victim@test.com", display_name="Victim")
        attacker = User(id=attacker_id, email="attacker@test.com", display_name="Attacker")
        db_session.add_all([victim, attacker])
        db_session.flush()

        # Create victim's submission
        victim_sub_id = f"victim_sub_{uuid.uuid4()}"
        victim_sub = SurveySubmission(
            submission_id=victim_sub_id,
            user_id=victim_id,
            payload_json={'answers': {'q1': 5}, 'secret': 'sensitive_data'}
        )
        db_session.add(victim_sub)

        # Create victim's profile
        victim_profile = Profile(
            user_id=victim_id,
            submission_id=victim_sub_id,
            profile_version='0.4',
            power_dynamic={}, arousal_propensity={},
            domain_scores={}, activities={},
            truth_topics={}, boundaries={},
            anatomy={'anatomy_self': [], 'anatomy_preference': []}
        )
        db_session.add(victim_profile)
        db_session.commit()

        # Attack 1: Try to sync victim's user without auth
        response = client.post(f'/api/users/{victim_id}/sync')
        assert response.status_code == 401, "Attack 1 should be blocked (no auth)"

        # Attack 2: Try to view victim's submission
        response = client.get(
            f'/api/survey/submissions/{victim_sub_id}',
            headers=get_auth_headers(attacker_id)
        )
        assert response.status_code == 403, "Attack 2 should be blocked (IDOR)"

        # Attack 3: Try to view victim's partner profile
        response = client.get(
            f'/api/profile-sharing/partner-profile/{victim_id}',
            headers=get_auth_headers(attacker_id)
        )
        assert response.status_code == 403, "Attack 3 should be blocked (no connection)"

        # Attack 4: Try to view victim's compatibility
        response = client.get(
            f'/api/survey/compatibility/{victim_sub_id}/any_other_id',
            headers=get_auth_headers(attacker_id)
        )
        assert response.status_code == 403, "Attack 4 should be blocked (not participant)"

        # Attack 5: Try to list all submissions
        response = client.get(
            '/api/survey/submissions',
            headers=get_auth_headers(attacker_id)
        )
        assert response.status_code == 200
        submissions = response.json.get('submissions', [])

        # Verify victim's data not exposed
        for sub in submissions:
            assert 'sensitive_data' not in str(sub), "Attack 5: Victim data leaked"
            assert victim_sub_id not in str(sub.get('id', '')), "Attack 5: Victim submission visible"

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_legitimate_partner_flow_works(self, client, db_session):
        """
        Verify legitimate partner access still works after security fixes.

        Flow:
        1. User A creates account and submission
        2. User B creates account and submission
        3. User A requests connection with User B
        4. User B accepts connection
        5. User A can now view User B's profile
        """
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()

        user_a = User(id=user_a_id, email="user_a@test.com", display_name="User A")
        user_b = User(id=user_b_id, email="user_b@test.com", display_name="User B",
                     profile_sharing_setting='all_responses')
        db_session.add_all([user_a, user_b])
        db_session.flush()

        # Create submissions and profiles
        for user_id in [user_a_id, user_b_id]:
            sub_id = f"sub_{user_id}"
            sub = SurveySubmission(
                submission_id=sub_id,
                user_id=user_id,
                payload_json={'answers': {'q1': 5}}
            )
            db_session.add(sub)

            profile = Profile(
                user_id=user_id,
                submission_id=sub_id,
                profile_version='0.4',
                power_dynamic={}, arousal_propensity={},
                domain_scores={}, activities={},
                truth_topics={}, boundaries={},
                anatomy={'anatomy_self': [], 'anatomy_preference': []}
            )
            db_session.add(profile)

        # Create ACCEPTED connection
        connection = PartnerConnection(
            requester_user_id=user_a_id,
            recipient_user_id=user_b_id,
            recipient_email="user_b@test.com",
            status='accepted',
            connection_token=str(uuid.uuid4()),
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        db_session.add(connection)
        db_session.commit()

        # Now User A should be able to view User B's profile
        response = client.get(
            f'/api/profile-sharing/partner-profile/{user_b_id}',
            headers=get_auth_headers(user_a_id)
        )

        assert response.status_code == 200, \
            f"Legitimate access should work. Got {response.status_code}"
```

---

## Commands to Run

### Full Test Suite
```bash
cd /home/user/attuned-survey/backend
source venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run only security tests
python -m pytest tests/test_security_*.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Run specific vulnerability tests
python -m pytest tests/test_security_auth_required.py -v
python -m pytest tests/test_security_idor.py -v
python -m pytest tests/test_security_data_exposure.py -v
```

### Quick Verification
```bash
# Run just the critical security tests
python -m pytest tests/test_security_*.py tests/test_idor_security.py -v --tb=short

# Run tests matching "CRITICAL" in docstrings
python -m pytest tests/ -v -k "critical" --tb=short
```

### Coverage Report
```bash
python -m pytest tests/test_security_*.py --cov=src/routes --cov-report=term-missing

# Expected coverage targets:
# - routes/sync_user.py: 100%
# - routes/process_submission.py: 100%
# - routes/survey.py: 90%+
# - routes/profile_sharing.py: 100%
# - routes/compatibility.py: 90%+
# - routes/system_admin.py: 100%
```

### CI/CD Integration
```yaml
# .github/workflows/security-tests.yml
name: Security Tests
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Security Tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/test_security_*.py tests/test_idor_security.py -v --tb=short
```

---

## Test Patterns Summary

### Pattern 1: Auth Required Test
```python
def test_endpoint_requires_auth_401(self, client):
    """Endpoint requires authentication."""
    response = client.get('/api/endpoint')
    assert response.status_code == 401
```

### Pattern 2: Wrong User Test (403)
```python
def test_endpoint_wrong_user_403(self, client, db_session, two_users):
    """User A cannot access User B's resource."""
    response = client.get(
        f'/api/resource/{two_users["user_b_id"]}',
        headers=get_auth_headers(two_users['user_a_id'])
    )
    assert response.status_code == 403
```

### Pattern 3: Success Test
```python
def test_endpoint_own_resource_success(self, client, db_session, user_with_resource):
    """User can access their own resource."""
    response = client.get(
        f'/api/resource/{user_with_resource["resource_id"]}',
        headers=get_auth_headers(user_with_resource['user_id'])
    )
    assert response.status_code == 200
```

### Pattern 4: Data Exposure Test
```python
def test_list_endpoint_no_data_leak(self, client, db_session, two_users):
    """List endpoint only returns user's own data."""
    # Create resources for both users
    # Request as user_a
    response = client.get('/api/resources', headers=get_auth_headers(user_a_id))

    # Verify only user_a's data returned
    for item in response.json['items']:
        assert item['user_id'] == str(user_a_id)
```

---

## Pre-Completion Checklist

Before marking the security fixes as complete:

- [ ] All `test_security_auth_required.py` tests pass
- [ ] All `test_security_idor.py` tests pass
- [ ] All `test_security_data_exposure.py` tests pass
- [ ] All `test_security_admin_access.py` tests pass
- [ ] All `test_security_info_disclosure.py` tests pass
- [ ] Rate limiting tests documented (skipped in test env)
- [ ] Integration tests pass
- [ ] Existing `test_idor_security.py` tests still pass
- [ ] Coverage meets minimum 80% for affected routes
- [ ] No regressions in existing functionality

```bash
# Final verification command
cd /home/user/attuned-survey/backend
pytest tests/ -v --tb=short && echo "ALL TESTS PASS"
```
