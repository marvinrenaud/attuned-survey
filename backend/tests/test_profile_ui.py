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

        # Route does not take user_id in path
        import jwt
        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
        auth_header = {'Authorization': f'Bearer {token}'}
        response = client.get(f'/api/users/profile-ui', headers=auth_header)
        
        # Verify
        assert response.status_code == 200
        data = response.get_json()
        assert data['user_id'] == user_id
        assert data['display_name'] == "Test User"
        assert data['submission_id'] == "sub_123"


def test_get_profile_ui_power_orientation_top_displays_leans_dom(client, db_session):
    """Test that Top orientation displays as 'Leans Dom' in profile-ui."""
    user_id = "123e4567-e89b-12d3-a456-426614174001"

    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.display_name = "Dom User"

    mock_profile = MagicMock(spec=Profile)
    mock_profile.user_id = user_id
    mock_profile.submission_id = "sub_dom"
    mock_profile.created_at = "2024-01-01"
    mock_profile.arousal_propensity = {}
    mock_profile.power_dynamic = {
        'orientation': 'Top',
        'top_score': 80,
        'bottom_score': 20,
        'interpretation': 'High confidence Top'
    }
    mock_profile.domain_scores = {}
    mock_profile.activities = {}
    mock_profile.boundaries = {}

    with patch('backend.src.models.user.User.query') as mock_user_query, \
         patch('backend.src.models.profile.Profile.query') as mock_profile_query:

        mock_user_query.get.return_value = mock_user
        mock_profile_query.filter_by.return_value.order_by.return_value.first.return_value = mock_profile

        import jwt
        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
        response = client.get('/api/users/profile-ui', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['general']['power']['label'] == 'Leans Dom'


def test_get_profile_ui_power_orientation_bottom_displays_leans_sub(client, db_session):
    """Test that Bottom orientation displays as 'Leans Sub' in profile-ui."""
    user_id = "123e4567-e89b-12d3-a456-426614174002"

    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.display_name = "Sub User"

    mock_profile = MagicMock(spec=Profile)
    mock_profile.user_id = user_id
    mock_profile.submission_id = "sub_sub"
    mock_profile.created_at = "2024-01-01"
    mock_profile.arousal_propensity = {}
    mock_profile.power_dynamic = {
        'orientation': 'Bottom',
        'top_score': 20,
        'bottom_score': 80,
        'interpretation': 'High confidence Bottom'
    }
    mock_profile.domain_scores = {}
    mock_profile.activities = {}
    mock_profile.boundaries = {}

    with patch('backend.src.models.user.User.query') as mock_user_query, \
         patch('backend.src.models.profile.Profile.query') as mock_profile_query:

        mock_user_query.get.return_value = mock_user
        mock_profile_query.filter_by.return_value.order_by.return_value.first.return_value = mock_profile

        import jwt
        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
        response = client.get('/api/users/profile-ui', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['general']['power']['label'] == 'Leans Sub'


def test_get_profile_ui_power_orientation_switch_unchanged(client, db_session):
    """Test that Switch orientation displays as 'Switch' (unchanged)."""
    user_id = "123e4567-e89b-12d3-a456-426614174003"

    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.display_name = "Switch User"

    mock_profile = MagicMock(spec=Profile)
    mock_profile.user_id = user_id
    mock_profile.submission_id = "sub_switch"
    mock_profile.created_at = "2024-01-01"
    mock_profile.arousal_propensity = {}
    mock_profile.power_dynamic = {
        'orientation': 'Switch',
        'top_score': 50,
        'bottom_score': 50,
        'interpretation': 'Switch'
    }
    mock_profile.domain_scores = {}
    mock_profile.activities = {}
    mock_profile.boundaries = {}

    with patch('backend.src.models.user.User.query') as mock_user_query, \
         patch('backend.src.models.profile.Profile.query') as mock_profile_query:

        mock_user_query.get.return_value = mock_user
        mock_profile_query.filter_by.return_value.order_by.return_value.first.return_value = mock_profile

        import jwt
        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
        response = client.get('/api/users/profile-ui', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['general']['power']['label'] == 'Switch'


def test_get_profile_ui_power_orientation_versatile_undefined(client, db_session):
    """Test that Versatile/Undefined orientation displays unchanged."""
    user_id = "123e4567-e89b-12d3-a456-426614174004"

    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.display_name = "Versatile User"

    mock_profile = MagicMock(spec=Profile)
    mock_profile.user_id = user_id
    mock_profile.submission_id = "sub_versatile"
    mock_profile.created_at = "2024-01-01"
    mock_profile.arousal_propensity = {}
    mock_profile.power_dynamic = {
        'orientation': 'Versatile/Undefined',
        'top_score': 20,
        'bottom_score': 20,
        'interpretation': 'Low engagement - still exploring preferences'
    }
    mock_profile.domain_scores = {}
    mock_profile.activities = {}
    mock_profile.boundaries = {}

    with patch('backend.src.models.user.User.query') as mock_user_query, \
         patch('backend.src.models.profile.Profile.query') as mock_profile_query:

        mock_user_query.get.return_value = mock_user
        mock_profile_query.filter_by.return_value.order_by.return_value.first.return_value = mock_profile

        import jwt
        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
        response = client.get('/api/users/profile-ui', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['general']['power']['label'] == 'Versatile/Undefined'


def test_get_profile_ui_power_orientation_unknown_falls_back_to_raw(client, db_session):
    """Test that unknown orientation values fall back to raw value."""
    user_id = "123e4567-e89b-12d3-a456-426614174005"

    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.display_name = "Unknown User"

    mock_profile = MagicMock(spec=Profile)
    mock_profile.user_id = user_id
    mock_profile.submission_id = "sub_unknown"
    mock_profile.created_at = "2024-01-01"
    mock_profile.arousal_propensity = {}
    mock_profile.power_dynamic = {
        'orientation': 'CustomOrientation',
        'top_score': 50,
        'bottom_score': 50,
        'interpretation': 'Unknown'
    }
    mock_profile.domain_scores = {}
    mock_profile.activities = {}
    mock_profile.boundaries = {}

    with patch('backend.src.models.user.User.query') as mock_user_query, \
         patch('backend.src.models.profile.Profile.query') as mock_profile_query:

        mock_user_query.get.return_value = mock_user
        mock_profile_query.filter_by.return_value.order_by.return_value.first.return_value = mock_profile

        import jwt
        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
        response = client.get('/api/users/profile-ui', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.get_json()
        # Unknown orientations fall back to raw value
        assert data['general']['power']['label'] == 'CustomOrientation'


def test_get_profile_ui_missing_orientation_defaults_to_switch(client, db_session):
    """Test that missing orientation key defaults to Switch label."""
    user_id = "123e4567-e89b-12d3-a456-426614174006"

    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.display_name = "No Orientation User"

    mock_profile = MagicMock(spec=Profile)
    mock_profile.user_id = user_id
    mock_profile.submission_id = "sub_no_orient"
    mock_profile.created_at = "2024-01-01"
    mock_profile.arousal_propensity = {}
    mock_profile.power_dynamic = {
        'top_score': 50,
        'bottom_score': 50
        # No 'orientation' key
    }
    mock_profile.domain_scores = {}
    mock_profile.activities = {}
    mock_profile.boundaries = {}

    with patch('backend.src.models.user.User.query') as mock_user_query, \
         patch('backend.src.models.profile.Profile.query') as mock_profile_query:

        mock_user_query.get.return_value = mock_user
        mock_profile_query.filter_by.return_value.order_by.return_value.first.return_value = mock_profile

        import jwt
        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
        response = client.get('/api/users/profile-ui', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.get_json()
        # Missing orientation defaults to 'Switch'
        assert data['general']['power']['label'] == 'Switch'


def test_get_profile_ui_empty_power_dynamic_defaults_to_switch(client, db_session):
    """Test that empty power_dynamic defaults to Switch label."""
    user_id = "123e4567-e89b-12d3-a456-426614174007"

    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.display_name = "Empty Power User"

    mock_profile = MagicMock(spec=Profile)
    mock_profile.user_id = user_id
    mock_profile.submission_id = "sub_empty_power"
    mock_profile.created_at = "2024-01-01"
    mock_profile.arousal_propensity = {}
    mock_profile.power_dynamic = {}  # Empty dict
    mock_profile.domain_scores = {}
    mock_profile.activities = {}
    mock_profile.boundaries = {}

    with patch('backend.src.models.user.User.query') as mock_user_query, \
         patch('backend.src.models.profile.Profile.query') as mock_profile_query:

        mock_user_query.get.return_value = mock_user
        mock_profile_query.filter_by.return_value.order_by.return_value.first.return_value = mock_profile

        import jwt
        token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
        response = client.get('/api/users/profile-ui', headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        data = response.get_json()
        # Empty power_dynamic defaults to 'Switch'
        assert data['general']['power']['label'] == 'Switch'
