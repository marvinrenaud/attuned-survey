import pytest
from unittest.mock import patch
import uuid
from backend.src.models.user import User
from backend.src.models.profile import Profile
from backend.src.extensions import db

@pytest.fixture
def auth_header():
    return {'Authorization': 'Bearer test-token'}

@patch('backend.src.middleware.auth.jwt.decode')
def test_domain_ordering(mock_jwt_decode, client, db_session, auth_header):
    """Test that domains are returned in the specific order: Sensation, Power, Connection, Exploration, Verbal."""
    
    # Setup User
    user_id = uuid.uuid4()
    mock_jwt_decode.return_value = {'sub': str(user_id)}
    
    # Mock DB queries
    with patch('backend.src.routes.profile_ui.User') as MockUser, \
         patch('backend.src.routes.profile_ui.Profile') as MockProfile:
        
        # Setup Mock User
        mock_user_instance = MockUser.query.get.return_value
        mock_user_instance.display_name = "Test User"
        
        # Setup Mock Profile
        mock_profile_instance = MockProfile.query.filter_by.return_value.order_by.return_value.first.return_value
        mock_profile_instance.submission_id = 'sub1'
        mock_profile_instance.domain_scores = {
            'sensation': 86,
            'connection': 100,
            'power': 75,
            'exploration': 80,
            'verbal': 62
        }
        # Required default fields for UI generation
        mock_profile_instance.arousal_propensity = {}
        mock_profile_instance.power_dynamic = {}
        mock_profile_instance.activities = {}
        mock_profile_instance.boundaries = {}

        # Execute
        response = client.get('/api/users/profile-ui', headers=auth_header)
        
        assert response.status_code == 200
        data = response.get_json()
        domains = data['general']['domains']
        
        # Extract order
        domain_names = [d['domain'] for d in domains]
        
        # Expected Order: Sensation > Power > Connection > Exploration > Verbal
        expected_order = ['Sensation', 'Power', 'Connection', 'Exploration', 'Verbal']
        
        # Check if order matches
        assert domain_names == expected_order, f"Expected {expected_order}, but got {domain_names}"
