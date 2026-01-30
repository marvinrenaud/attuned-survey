"""
Authentication tests for /api/survey/* endpoints.

This file tests that protected survey endpoints correctly require authentication.
It focuses on endpoints that are NOT already covered in test_survey_auth.py.
"""

import pytest
import uuid
import os
from unittest.mock import patch
import jwt

from backend.src.models.user import User
from backend.src.extensions import db


def create_token(user_id: str) -> str:
    """Create a valid JWT token for testing."""
    return jwt.encode(
        {"sub": str(user_id), "aud": "authenticated"},
        "test-secret-key",
        algorithm="HS256"
    )


def get_auth_headers(user_id: str) -> dict:
    """Get authorization headers with a valid token."""
    return {'Authorization': f'Bearer {create_token(user_id)}'}


class TestSurveyBaseline:
    """Test /api/survey/baseline endpoint authentication."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_get_baseline_unauthorized(self, client):
        """GET /api/survey/baseline requires auth."""
        response = client.get('/api/survey/baseline')
        assert response.status_code == 401

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_post_baseline_unauthorized(self, client):
        """POST /api/survey/baseline requires auth."""
        response = client.post('/api/survey/baseline', json={'id': 'test-submission-id'})
        assert response.status_code == 401

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_delete_baseline_unauthorized(self, client):
        """DELETE /api/survey/baseline requires auth."""
        response = client.delete('/api/survey/baseline')
        assert response.status_code == 401


class TestSurveyExport:
    """Test /api/survey/export endpoint authentication."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_export_unauthorized(self, client):
        """GET /api/survey/export requires auth."""
        response = client.get('/api/survey/export')
        assert response.status_code == 401


class TestSurveySubmissions:
    """Test /api/survey/submissions endpoint authentication."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_get_submissions_unauthorized(self, client):
        """GET /api/survey/submissions requires auth."""
        response = client.get('/api/survey/submissions')
        assert response.status_code == 401

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_get_single_submission_unauthorized(self, client):
        """GET /api/survey/submissions/<id> requires auth."""
        response = client.get('/api/survey/submissions/test-submission-123')
        assert response.status_code == 401


class TestSurveyCompatibility:
    """Test /api/survey/compatibility endpoint authentication."""

    @patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
    def test_get_compatibility_unauthorized(self, client):
        """GET /api/survey/compatibility/<source_id>/<target_id> requires auth."""
        response = client.get('/api/survey/compatibility/source-123/target-456')
        assert response.status_code == 401
