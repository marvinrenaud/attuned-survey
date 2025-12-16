import pytest
from unittest.mock import patch, MagicMock
from backend.src.models.user import User
from backend.src.models.profile import Profile

def test_get_profile_ui_includes_display_name(client, db_session):
    """Test that profile-ui endpoint returns display_name."""
    # Setup
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    
    # Mock User
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.display_name = "Test User"
    
    # Mock Profile
    mock_profile = MagicMock(spec=Profile)
    mock_profile.user_id = user_id
    mock_profile.submission_id = "sub_123"
    mock_profile.created_at = "2024-01-01"
    # Add required attributes to avoid AttributeError
    mock_profile.arousal_propensity = {}
    mock_profile.power_dynamic = {}
    mock_profile.domain_scores = {}
    mock_profile.activities = {}
    mock_profile.boundaries = {}

    # Patch the queries
    with patch('backend.src.models.user.User.query') as mock_user_query, \
         patch('backend.src.models.profile.Profile.query') as mock_profile_query:
        
        mock_user_query.get.return_value = mock_user
        
        # Mock chain: filter_by -> order_by -> first
        mock_profile_query.filter_by.return_value.order_by.return_value.first.return_value = mock_profile

        # Execute
        response = client.get(f'/api/users/{user_id}/profile-ui')
        
        # Verify
        assert response.status_code == 200
        data = response.get_json()
        assert data['user_id'] == user_id
        assert data['display_name'] == "Test User"
        assert data['submission_id'] == "sub_123"
