
import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch
from src.models.user import User

@pytest.fixture
def app_context(app):
    """Ensure app context is pushed"""
    with app.app_context():
        yield

from datetime import datetime

@pytest.fixture
def mock_user(db_session, test_user_data):
    """Create a mock user for testing"""
    user = User(
        id=test_user_data['id'],
        email=test_user_data['email'],
        display_name=test_user_data['display_name'],
        auth_provider=test_user_data['auth_provider'],
        demographics=test_user_data['demographics'],
        subscription_tier='free',
        daily_activity_count=0,
        daily_activity_reset_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_login_at=datetime.utcnow(),
        subscription_expires_at=None
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def mock_auth_user(mock_user):
    """Fixture to ensure the user used in auth matches database"""
    return mock_user

def test_validate_subscription_premium(client, app_context, mock_auth_user, db_session):
    """Test subscription validation for premium user"""
    # Setup premium user
    mock_auth_user.subscription_tier = 'premium'
    db_session.add(mock_auth_user)
    db_session.commit()
    
    # Authenticate as this user
    with patch('src.middleware.auth.jwt.decode') as mock_decode:
        mock_decode.return_value = {"sub": str(mock_auth_user.id)}
        
        response = client.get(
            f'/api/subscriptions/validate/{mock_auth_user.id}',
            headers={'Authorization': 'Bearer valid-token'}
        )
        
        if response.status_code != 200:
            print(f"DEBUG_FAIL_RESPONSE_DATA: {response.data}")
            # print(f"DEBUG_FAIL_RESPONSE_JSON: {response.get_json()}")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['is_premium'] is True
        assert data['subscription_tier'] == 'premium'

def test_validate_subscription_free(client, app_context, mock_auth_user, db_session):
    """Test subscription validation for free user"""
    # Setup free user
    mock_auth_user.subscription_tier = 'free'
    db_session.add(mock_auth_user)
    db_session.commit()
    
    with patch('src.middleware.auth.jwt.decode') as mock_decode:
        mock_decode.return_value = {"sub": str(mock_auth_user.id)}
        
        response = client.get(
            f'/api/subscriptions/validate/{mock_auth_user.id}',
            headers={'Authorization': 'Bearer valid-token'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['is_premium'] is False
        assert data['subscription_tier'] == 'free'

def test_check_daily_limit_enforced(client, app_context, mock_auth_user, db_session):
    """Test daily limit enforcement for free tier"""
    mock_auth_user.subscription_tier = 'free'
    mock_auth_user.daily_activity_count = 25  # At limit
    db_session.add(mock_auth_user)
    db_session.commit()
    
    with patch('src.middleware.auth.jwt.decode') as mock_decode:
        mock_decode.return_value = {"sub": str(mock_auth_user.id)}
        
        response = client.get(
            f'/api/subscriptions/check-limit/{mock_auth_user.id}',
            headers={'Authorization': 'Bearer valid-token'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['limit_reached'] is True
        assert data['remaining'] == 0

def test_check_daily_limit_premium_unlimited(client, app_context, mock_auth_user, db_session):
    """Test that premium users ignore limits"""
    mock_auth_user.subscription_tier = 'premium'
    mock_auth_user.daily_activity_count = 100  # Over normal limit
    db_session.add(mock_auth_user)
    db_session.commit()
    
    with patch('src.middleware.auth.jwt.decode') as mock_decode:
        mock_decode.return_value = {"sub": str(mock_auth_user.id)}
        
        response = client.get(
            f'/api/subscriptions/check-limit/{mock_auth_user.id}',
            headers={'Authorization': 'Bearer valid-token'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['has_limit'] is False
        assert data['limit_reached'] is False

def test_increment_activity_count(client, app_context, mock_auth_user, db_session):
    """Test activity counter increment"""
    mock_auth_user.subscription_tier = 'free'
    mock_auth_user.daily_activity_count = 0
    db_session.add(mock_auth_user)
    db_session.commit()
    
    with patch('src.middleware.auth.jwt.decode') as mock_decode:
        mock_decode.return_value = {"sub": str(mock_auth_user.id)}
        
        response = client.post(
            f'/api/subscriptions/increment-activity/{mock_auth_user.id}',
            headers={'Authorization': 'Bearer valid-token'}
        )
        
        assert response.status_code == 200
        
        # Verify DB update
        db_session.refresh(mock_auth_user)
        assert mock_auth_user.daily_activity_count == 1
