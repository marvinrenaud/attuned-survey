"""
Authentication tests for /api/profile-sharing/* endpoints.
"""

import pytest
import uuid


class TestProfileSharingAuth:
    """Test profile sharing endpoints require auth."""

    def test_get_settings_unauthorized(self, client):
        """GET /api/profile-sharing/settings requires auth."""
        response = client.get('/api/profile-sharing/settings')
        assert response.status_code == 401

    def test_get_settings_invalid_token(self, client):
        """GET /api/profile-sharing/settings rejects invalid token."""
        response = client.get(
            '/api/profile-sharing/settings',
            headers={'Authorization': 'Bearer invalid-token-here'}
        )
        assert response.status_code == 401

    def test_put_settings_unauthorized(self, client):
        """PUT /api/profile-sharing/settings requires auth."""
        response = client.put(
            '/api/profile-sharing/settings',
            json={'profile_sharing_setting': 'all_responses'}
        )
        assert response.status_code == 401

    def test_put_settings_invalid_token(self, client):
        """PUT /api/profile-sharing/settings rejects invalid token."""
        response = client.put(
            '/api/profile-sharing/settings',
            json={'profile_sharing_setting': 'all_responses'},
            headers={'Authorization': 'Bearer invalid-token-here'}
        )
        assert response.status_code == 401

    def test_get_partner_profile_unauthorized(self, client):
        """GET /api/profile-sharing/partner-profile/<id> requires auth."""
        partner_id = str(uuid.uuid4())
        response = client.get(f'/api/profile-sharing/partner-profile/{partner_id}')
        assert response.status_code == 401

    def test_get_partner_profile_invalid_token(self, client):
        """GET /api/profile-sharing/partner-profile/<id> rejects invalid token."""
        partner_id = str(uuid.uuid4())
        response = client.get(
            f'/api/profile-sharing/partner-profile/{partner_id}',
            headers={'Authorization': 'Bearer invalid-token-here'}
        )
        assert response.status_code == 401
