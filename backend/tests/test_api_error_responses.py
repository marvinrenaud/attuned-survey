"""
Tests for consistent API error response shapes.

These tests verify that endpoints return consistent response shapes on errors,
preventing frontend crashes when the backend returns 500 errors.

Issue: Frontend (FlutterFlow) expects certain fields (e.g., 'partners', 'connections')
to always exist and crashes when calling .toList() on null.
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.routes.partners import partners_bp
from src.routes.recommendations import bp as recommendations_bp
from src.extensions import db
import jwt
import os


@pytest.fixture
def app():
    """Create Flask app with required blueprints for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    app.register_blueprint(partners_bp)
    app.register_blueprint(recommendations_bp)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def auth_header():
    """Generate valid JWT auth header."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = jwt.encode(
        {"sub": user_id, "aud": "authenticated"},
        "test-secret-key",
        algorithm="HS256"
    )
    return {'Authorization': f'Bearer {token}'}


class TestPartnersRememberedErrorResponse:
    """Tests for /api/partners/remembered error response consistency."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_remembered_partners_error_returns_empty_array(self, client, auth_header):
        """
        When /api/partners/remembered returns 500, response must include 'partners': [].

        This prevents frontend crashes when calling .toList() on the partners field.
        """
        with patch('src.routes.partners.RememberedPartner.query') as mock_query:
            # Simulate database error
            mock_query.filter_by.side_effect = Exception("Database connection failed")

            response = client.get('/api/partners/remembered', headers=auth_header)

            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert 'partners' in data, "Error response must include 'partners' field"
            assert data['partners'] == [], "Error response 'partners' must be empty array"


class TestPartnersConnectionsErrorResponse:
    """Tests for /api/partners/connections error response consistency."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_connections_error_returns_empty_array(self, client, auth_header):
        """
        When /api/partners/connections returns 500, response must include 'connections': [].
        """
        with patch('src.routes.partners.User.query') as mock_user_query, \
             patch('src.routes.partners.PartnerConnection.query') as mock_conn_query:

            mock_user = MagicMock(id="123e4567-e89b-12d3-a456-426614174000", email="test@example.com")
            mock_user_query.get.return_value = mock_user

            # Simulate database error on connection query
            mock_conn_query.filter.side_effect = Exception("Database connection failed")

            response = client.get('/api/partners/connections', headers=auth_header)

            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert 'connections' in data, "Error response must include 'connections' field"
            assert data['connections'] == [], "Error response 'connections' must be empty array"


class TestRecommendationsErrorResponse:
    """Tests for /api/recommendations/<session_id> error response consistency."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_recommendations_error_returns_consistent_shape(self, client, auth_header):
        """
        When /api/recommendations/<session_id> returns 500, response must include
        'activities': [], 'session': None, and 'session_id'.
        """
        session_id = "test-session-123"

        with patch('src.routes.recommendations.repository') as mock_repo:
            # Simulate error when getting session
            mock_repo.get_session.side_effect = Exception("Database connection failed")

            response = client.get(
                f'/api/recommendations/{session_id}',
                headers=auth_header
            )

            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert 'activities' in data, "Error response must include 'activities' field"
            assert data['activities'] == [], "Error response 'activities' must be empty array"
            assert 'session' in data, "Error response must include 'session' field"
            assert data['session'] is None, "Error response 'session' must be None"
            assert 'session_id' in data, "Error response must include 'session_id' field"
            assert data['session_id'] == session_id, "Error response 'session_id' must match request"
