"""
Tests for promo code validation endpoint.

TDD: These tests are written BEFORE implementation.
"""
import os
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from src.models.user import User
from src.models.influencer import Influencer
from src.models.promo_code import PromoCode
from src.models.promo_redemption import PromoRedemption


@pytest.fixture
def app_context(app):
    """Ensure app context is pushed"""
    with app.app_context():
        yield


@pytest.fixture
def test_user(db_session, test_user_data):
    """Create a test user"""
    user = User(
        id=test_user_data['id'],
        email=test_user_data['email'],
        display_name=test_user_data['display_name'],
        auth_provider=test_user_data['auth_provider'],
        demographics=test_user_data['demographics'],
        subscription_tier='free',
        lifetime_activity_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def influencer(db_session):
    """Create a test influencer"""
    inf = Influencer(
        name='Vanessa Marin',
        email='vanessa@example.com',
        platform='instagram',
        status='active',
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(inf)
    db_session.commit()
    return inf


@pytest.fixture
def valid_promo_code(db_session, influencer):
    """Create a valid active promo code"""
    code = PromoCode(
        influencer_id=influencer.id,
        code='VANESSA',
        discount_percent=20,
        revenuecat_offering_id='discounted_20_percent',
        is_active=True,
        redemption_count=0,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(code)
    db_session.commit()
    return code


@pytest.fixture
def expired_promo_code(db_session, influencer):
    """Create an expired promo code"""
    code = PromoCode(
        influencer_id=influencer.id,
        code='EXPIRED',
        discount_percent=15,
        revenuecat_offering_id='discounted_15_percent',
        is_active=True,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired yesterday
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(code)
    db_session.commit()
    return code


@pytest.fixture
def maxed_promo_code(db_session, influencer):
    """Create a promo code that has reached max redemptions"""
    code = PromoCode(
        influencer_id=influencer.id,
        code='MAXED',
        discount_percent=10,
        revenuecat_offering_id='discounted_10_percent',
        is_active=True,
        max_redemptions=100,
        redemption_count=100,  # At limit
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(code)
    db_session.commit()
    return code


@pytest.fixture
def inactive_promo_code(db_session, influencer):
    """Create an inactive promo code"""
    code = PromoCode(
        influencer_id=influencer.id,
        code='INACTIVE',
        discount_percent=20,
        revenuecat_offering_id='discounted_20_percent',
        is_active=False,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(code)
    db_session.commit()
    return code


class TestPromoValidation:
    """Tests for POST /api/promo/validate"""

    def test_validate_requires_auth(self, client, app_context):
        """401 without token"""
        response = client.post(
            '/api/promo/validate',
            json={'code': 'VANESSA'}
        )
        assert response.status_code == 401

    def test_validate_with_valid_code(self, client, app_context, test_user, valid_promo_code, db_session):
        """Returns offering_id and discount info for valid code"""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'VANESSA'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is True
            assert data['code'] == 'VANESSA'
            assert data['discount_percent'] == 20
            assert data['influencer_name'] == 'Vanessa Marin'
            assert data['offering_id'] == 'discounted_20_percent'

    def test_validate_code_not_found(self, client, app_context, test_user, db_session):
        """Returns valid=false for non-existent code"""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'NONEXISTENT'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is False
            assert data['error'] == 'Code not found'

    def test_validate_expired_code(self, client, app_context, test_user, expired_promo_code, db_session):
        """Returns valid=false for expired code"""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'EXPIRED'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is False
            assert data['error'] == 'Code has expired'

    def test_validate_inactive_code(self, client, app_context, test_user, inactive_promo_code, db_session):
        """Returns valid=false for inactive code"""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'INACTIVE'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is False
            assert data['error'] == 'Code is inactive'

    def test_validate_max_redemptions_reached(self, client, app_context, test_user, maxed_promo_code, db_session):
        """Returns valid=false when max redemptions reached"""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'MAXED'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is False
            assert data['error'] == 'Maximum redemptions reached'

    def test_validate_already_used_by_user(self, client, app_context, test_user, valid_promo_code, db_session):
        """Returns valid=false if user already redeemed this code for a DISCOUNTED product"""
        # Create existing redemption for DISCOUNTED product
        # Note: Only blocks if user actually got the discount (product has 'discounted' in name)
        redemption = PromoRedemption(
            promo_code_id=valid_promo_code.id,
            user_id=test_user.id,
            subscription_product='attuned_monthly_discounted',  # Must be discounted to block
            discounted_price=3.99,
            redeemed_at=datetime.now(timezone.utc),
        )
        db_session.add(redemption)
        db_session.commit()

        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'VANESSA'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is False
            assert data['error'] == 'Code already used'

    def test_validate_sets_pending_promo_code(self, client, app_context, test_user, valid_promo_code, db_session):
        """User.pending_promo_code updated on successful validation"""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'VANESSA'}
            )

            assert response.status_code == 200

            # Verify pending_promo_code was set
            db_session.refresh(test_user)
            assert test_user.pending_promo_code == 'VANESSA'

    def test_validate_case_insensitive(self, client, app_context, test_user, valid_promo_code, db_session):
        """'vanessa' matches 'VANESSA'"""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'vanessa'}  # lowercase
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is True
            assert data['code'] == 'VANESSA'  # Returns original case

    def test_validate_overwrites_pending_code(self, client, app_context, test_user, valid_promo_code, db_session, influencer):
        """New validation replaces previous pending code"""
        # Set initial pending code
        test_user.pending_promo_code = 'OLD_CODE'
        db_session.commit()

        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'VANESSA'}
            )

            assert response.status_code == 200

            # Verify pending_promo_code was overwritten
            db_session.refresh(test_user)
            assert test_user.pending_promo_code == 'VANESSA'

    def test_validate_missing_code(self, client, app_context, test_user, db_session):
        """Returns error when code is missing from request"""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={}
            )

            assert response.status_code == 400
