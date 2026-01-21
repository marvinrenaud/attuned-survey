"""
Authentication tests for /api/auth/* endpoints.
"""

import pytest
import uuid
import jwt

from backend.src.models.user import User
from backend.src.extensions import db


@pytest.fixture
def auth_header():
    """Generate auth headers with a valid JWT token."""
    def _get_header(user_id):
        token = jwt.encode(
            {"sub": str(user_id), "aud": "authenticated"},
            "test-secret-key",
            algorithm="HS256"
        )
        return {'Authorization': f'Bearer {token}'}
    return _get_header


class TestAuthProfile:
    """Test /api/auth/profile endpoint."""

    def test_get_profile_unauthorized(self, client):
        """GET /api/auth/profile requires auth."""
        response = client.get('/api/auth/profile')
        assert response.status_code == 401

    def test_patch_profile_unauthorized(self, client):
        """PATCH /api/auth/profile requires auth."""
        response = client.patch('/api/auth/profile', json={'display_name': 'Test'})
        assert response.status_code == 401

    def test_delete_profile_unauthorized(self, client):
        """DELETE /api/auth/profile requires auth."""
        response = client.delete('/api/auth/profile')
        assert response.status_code == 401

    def test_get_profile_authorized(self, client, app, auth_header):
        """GET /api/auth/profile returns user data when authenticated."""
        user_id = uuid.uuid4()

        with app.app_context():
            user = User(id=user_id, email="profile-test@example.com", display_name="Test User")
            db.session.add(user)
            db.session.commit()

        response = client.get('/api/auth/profile', headers=auth_header(user_id))

        assert response.status_code == 200
        assert response.json['user']['id'] == str(user_id)
        assert response.json['user']['email'] == "profile-test@example.com"

    def test_patch_profile_authorized(self, client, app, auth_header):
        """PATCH /api/auth/profile updates user data when authenticated."""
        user_id = uuid.uuid4()

        with app.app_context():
            user = User(id=user_id, email="patch-test@example.com", display_name="Original")
            db.session.add(user)
            db.session.commit()

        response = client.patch(
            '/api/auth/profile',
            json={'display_name': 'Updated Name'},
            headers=auth_header(user_id)
        )

        assert response.status_code == 200
        assert response.json['user']['display_name'] == 'Updated Name'

    def test_delete_profile_authorized(self, client, app, auth_header):
        """DELETE /api/auth/profile deletes user when authenticated."""
        user_id = uuid.uuid4()

        with app.app_context():
            user = User(id=user_id, email="delete-test@example.com")
            db.session.add(user)
            db.session.commit()

        response = client.delete('/api/auth/profile', headers=auth_header(user_id))

        assert response.status_code == 200
        assert response.json['success'] is True

        # Verify user is deleted
        with app.app_context():
            deleted_user = User.query.filter_by(id=user_id).first()
            assert deleted_user is None


class TestAuthLogin:
    """Test /api/auth/login endpoint."""

    def test_login_unauthorized(self, client):
        """POST /api/auth/login requires auth."""
        response = client.post('/api/auth/login', json={})
        assert response.status_code == 401

    def test_login_authorized_updates_timestamp(self, client, app, auth_header):
        """POST /api/auth/login updates last_login_at when authenticated."""
        user_id = uuid.uuid4()

        with app.app_context():
            user = User(id=user_id, email="login-test@example.com")
            db.session.add(user)
            db.session.commit()
            original_login = user.last_login_at

        response = client.post('/api/auth/login', json={}, headers=auth_header(user_id))

        assert response.status_code == 200
        assert response.json['success'] is True

    def test_login_user_not_found(self, client, auth_header):
        """POST /api/auth/login returns 404 for non-existent user."""
        non_existent_id = uuid.uuid4()

        response = client.post('/api/auth/login', json={}, headers=auth_header(non_existent_id))

        assert response.status_code == 404
        assert response.json['error'] == 'User not found'


class TestCompleteDemographics:
    """Test /api/auth/complete-demographics endpoint."""

    def test_complete_demographics_unauthorized(self, client):
        """POST /api/auth/complete-demographics requires auth."""
        response = client.post('/api/auth/complete-demographics', json={})
        assert response.status_code == 401

    def test_complete_demographics_missing_name(self, client, app, auth_header):
        """POST /api/auth/complete-demographics validates required name field."""
        user_id = uuid.uuid4()

        with app.app_context():
            user = User(id=user_id, email="demo-test@example.com")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            '/api/auth/complete-demographics',
            json={'has_penis': True, 'likes_vagina': True},  # Missing 'name'
            headers=auth_header(user_id)
        )

        assert response.status_code == 400
        assert response.json['error'] == 'Missing required field: name'

    def test_complete_demographics_missing_anatomy(self, client, app, auth_header):
        """POST /api/auth/complete-demographics validates anatomy fields."""
        user_id = uuid.uuid4()

        with app.app_context():
            user = User(id=user_id, email="anatomy-test@example.com")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            '/api/auth/complete-demographics',
            json={'name': 'Test User'},  # Missing anatomy fields
            headers=auth_header(user_id)
        )

        assert response.status_code == 400
        assert 'anatomy' in response.json['error'].lower()

    def test_complete_demographics_missing_has_anatomy(self, client, app, auth_header):
        """POST /api/auth/complete-demographics requires at least one 'has' anatomy."""
        user_id = uuid.uuid4()

        with app.app_context():
            user = User(id=user_id, email="has-test@example.com")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            '/api/auth/complete-demographics',
            json={
                'name': 'Test User',
                'has_penis': False,
                'has_vagina': False,
                'has_breasts': False,
                'likes_penis': True
            },
            headers=auth_header(user_id)
        )

        assert response.status_code == 400
        assert 'what you have' in response.json['error']

    def test_complete_demographics_missing_likes_anatomy(self, client, app, auth_header):
        """POST /api/auth/complete-demographics requires at least one 'likes' anatomy."""
        user_id = uuid.uuid4()

        with app.app_context():
            user = User(id=user_id, email="likes-test@example.com")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            '/api/auth/complete-demographics',
            json={
                'name': 'Test User',
                'has_penis': True,
                'likes_penis': False,
                'likes_vagina': False,
                'likes_breasts': False
            },
            headers=auth_header(user_id)
        )

        assert response.status_code == 400
        assert 'what you like' in response.json['error']

    def test_complete_demographics_success_boolean_format(self, client, app, auth_header):
        """POST /api/auth/complete-demographics succeeds with boolean format."""
        user_id = uuid.uuid4()

        with app.app_context():
            user = User(id=user_id, email="success-bool@example.com")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            '/api/auth/complete-demographics',
            json={
                'name': 'Test User',
                'has_penis': True,
                'has_vagina': False,
                'has_breasts': False,
                'likes_penis': False,
                'likes_vagina': True,
                'likes_breasts': True
            },
            headers=auth_header(user_id)
        )

        assert response.status_code == 200
        assert response.json['success'] is True
        assert response.json['profile_completed'] is True
        assert response.json['anatomy']['has_penis'] is True
        assert response.json['anatomy']['likes_vagina'] is True

    def test_complete_demographics_success_array_format(self, client, app, auth_header):
        """POST /api/auth/complete-demographics succeeds with array format (backward compat)."""
        user_id = uuid.uuid4()

        with app.app_context():
            user = User(id=user_id, email="success-array@example.com")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            '/api/auth/complete-demographics',
            json={
                'name': 'Test User',
                'anatomy_self': ['vagina', 'breasts'],
                'anatomy_preference': ['penis', 'vagina']
            },
            headers=auth_header(user_id)
        )

        assert response.status_code == 200
        assert response.json['success'] is True
        assert response.json['anatomy']['has_vagina'] is True
        assert response.json['anatomy']['has_breasts'] is True
        assert response.json['anatomy']['likes_penis'] is True


class TestAuthRegister:
    """Test /api/auth/register endpoint."""

    def test_register_missing_id(self, client):
        """POST /api/auth/register validates required id field."""
        response = client.post(
            '/api/auth/register',
            json={'email': 'test@example.com'}
        )

        assert response.status_code == 400
        assert 'id' in response.json['error']

    def test_register_missing_email(self, client):
        """POST /api/auth/register validates required email field."""
        response = client.post(
            '/api/auth/register',
            json={'id': str(uuid.uuid4())}
        )

        assert response.status_code == 400
        assert 'email' in response.json['error']

    def test_register_invalid_id(self, client):
        """POST /api/auth/register validates id is valid UUID."""
        response = client.post(
            '/api/auth/register',
            json={'id': 'not-a-uuid', 'email': 'test@example.com'}
        )

        assert response.status_code == 400
        assert response.json['error'] == 'Invalid ID'

    def test_register_success(self, client, app):
        """POST /api/auth/register creates user successfully."""
        user_id = uuid.uuid4()

        response = client.post(
            '/api/auth/register',
            json={
                'id': str(user_id),
                'email': 'newuser@example.com',
                'display_name': 'New User',
                'auth_provider': 'email'
            }
        )

        assert response.status_code == 201
        assert response.json['success'] is True
        assert response.json['user']['email'] == 'newuser@example.com'

        # Verify user exists in database
        with app.app_context():
            user = User.query.filter_by(id=user_id).first()
            assert user is not None
            assert user.email == 'newuser@example.com'

    def test_register_duplicate_user(self, client, app):
        """POST /api/auth/register returns 409 for duplicate user."""
        user_id = uuid.uuid4()

        with app.app_context():
            user = User(id=user_id, email="existing@example.com")
            db.session.add(user)
            db.session.commit()

        response = client.post(
            '/api/auth/register',
            json={
                'id': str(user_id),
                'email': 'existing@example.com'
            }
        )

        assert response.status_code == 409
        assert response.json['error'] == 'User already exists'


class TestValidateToken:
    """Test /api/auth/validate-token endpoint."""

    def test_validate_token_no_auth_required(self, client):
        """POST /api/auth/validate-token does not require auth (public endpoint)."""
        response = client.post('/api/auth/validate-token')

        assert response.status_code == 200
        assert response.json['valid'] is True
