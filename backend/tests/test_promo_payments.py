"""
Comprehensive tests for promo code and payments functionality.

This test suite covers:
- Promo code validation (including the discounted vs non-discounted fix)
- Promo attribution during purchase webhooks
- Webhook integration with promo codes

TDD: Tests marked with # BUG FIX are for the "Code already used" bug fix.
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from src.models.user import User
from src.models.influencer import Influencer
from src.models.promo_code import PromoCode
from src.models.promo_redemption import PromoRedemption
from src.services.subscription_service import SubscriptionService


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def app_context(app):
    """Ensure app context is pushed."""
    with app.app_context():
        yield


@pytest.fixture
def test_user(db_session, test_user_data):
    """Create a test user."""
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
    """Create a test influencer."""
    inf = Influencer(
        name='Test Influencer',
        email='influencer@example.com',
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
    """Create a valid active promo code."""
    code = PromoCode(
        influencer_id=influencer.id,
        code='TESTPROMO',
        discount_percent=20,
        revenuecat_offering_id='discounted_20_percent',
        is_active=True,
        redemption_count=0,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(code)
    db_session.commit()
    return code


def make_event(event_type, **kwargs):
    """Helper to create RevenueCat event dicts."""
    default_expiration = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp() * 1000)
    return {
        'type': event_type,
        'id': f'evt_{uuid.uuid4().hex[:12]}',
        'app_user_id': kwargs.get('app_user_id', str(uuid.uuid4())),
        'product_id': kwargs.get('product_id', 'attuned_monthly'),
        'expiration_at_ms': kwargs.get('expiration_at_ms', default_expiration),
        'store': kwargs.get('store', 'APP_STORE'),
        'price': kwargs.get('price', 4.99),
        **{k: v for k, v in kwargs.items() if k not in ['app_user_id', 'product_id', 'expiration_at_ms', 'store', 'price']}
    }


# =============================================================================
# TestPromoValidation - Endpoint tests for /api/promo/validate
# =============================================================================

class TestPromoValidation:
    """Tests for POST /api/promo/validate endpoint."""

    def test_validate_returns_401_without_auth(self, client, app_context):
        """Endpoint requires authentication."""
        response = client.post(
            '/api/promo/validate',
            json={'code': 'TESTPROMO'}
        )
        assert response.status_code == 401

    def test_validate_returns_400_without_code(self, client, app_context, test_user, db_session):
        """Missing code parameter returns 400."""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={}
            )

            assert response.status_code == 400

    def test_validate_returns_invalid_for_unknown_code(self, client, app_context, test_user, db_session):
        """Unknown code returns valid=false."""
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

    def test_validate_returns_valid_for_active_code(self, client, app_context, test_user, valid_promo_code, db_session):
        """Valid active code returns success with offering info."""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'TESTPROMO'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is True
            assert data['code'] == 'TESTPROMO'
            assert data['discount_percent'] == 20
            assert data['offering_id'] == 'discounted_20_percent'

    def test_validate_sets_pending_promo_code_on_user(self, client, app_context, test_user, valid_promo_code, db_session):
        """Successful validation sets user.pending_promo_code."""
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'TESTPROMO'}
            )

            assert response.status_code == 200
            db_session.refresh(test_user)
            assert test_user.pending_promo_code == 'TESTPROMO'

    # BUG FIX: These tests verify the fix for "Code already used" bug
    def test_validate_allows_reuse_if_no_discounted_redemption(self, client, app_context, test_user, valid_promo_code, db_session):
        """
        BUG FIX: User with redemption for NON-DISCOUNTED product can reuse code.

        Scenario: User validated code, but then bought full-price product.
        They should be able to use the promo code again.
        """
        # Create existing redemption for NON-discounted product
        redemption = PromoRedemption(
            promo_code_id=valid_promo_code.id,
            user_id=test_user.id,
            subscription_product='attuned_monthly_web',  # NON-discounted!
            discounted_price=4.99,  # Full price
            redeemed_at=datetime.now(timezone.utc),
        )
        db_session.add(redemption)
        db_session.commit()

        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'TESTPROMO'}
            )

            assert response.status_code == 200
            data = response.get_json()
            # Should be VALID - user never got the discount
            assert data['valid'] is True, f"Expected valid=True, got {data}"

    def test_validate_blocks_if_discounted_redemption_exists(self, client, app_context, test_user, valid_promo_code, db_session):
        """
        BUG FIX: User with redemption for DISCOUNTED product cannot reuse code.

        Scenario: User validated code and bought discounted product.
        They should NOT be able to use the code again.
        """
        # Create existing redemption for DISCOUNTED product
        redemption = PromoRedemption(
            promo_code_id=valid_promo_code.id,
            user_id=test_user.id,
            subscription_product='attuned_monthly_web_discounted',  # DISCOUNTED!
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
                json={'code': 'TESTPROMO'}
            )

            assert response.status_code == 200
            data = response.get_json()
            # Should be INVALID - user already got the discount
            assert data['valid'] is False
            assert data['error'] == 'Code already used'


# =============================================================================
# TestPromoAttribution - Service layer tests for redemption recording
# =============================================================================

class TestPromoAttribution:
    """Tests for promo code attribution during INITIAL_PURCHASE."""

    def test_attribution_creates_redemption_for_discounted_product(self, app_context, db_session, test_user, valid_promo_code):
        """
        BUG FIX: Redemption is created when user purchases DISCOUNTED product.
        """
        test_user.pending_promo_code = valid_promo_code.code
        db_session.commit()

        event = make_event(
            'INITIAL_PURCHASE',
            product_id='attuned_monthly_web_discounted',  # DISCOUNTED
            price=3.99
        )
        SubscriptionService.process_webhook_event(test_user, event)

        # Redemption should be created
        redemption = db_session.query(PromoRedemption).filter_by(user_id=test_user.id).first()
        assert redemption is not None
        assert redemption.subscription_product == 'attuned_monthly_web_discounted'

        # User fields should be updated
        assert test_user.promo_code_used == valid_promo_code.code
        assert test_user.pending_promo_code is None

    def test_attribution_skips_redemption_for_non_discounted_product(self, app_context, db_session, test_user, valid_promo_code):
        """
        BUG FIX: NO redemption when user purchases NON-DISCOUNTED product.

        This is the core fix - user had pending code but bought full price.
        """
        test_user.pending_promo_code = valid_promo_code.code
        db_session.commit()

        event = make_event(
            'INITIAL_PURCHASE',
            product_id='attuned_monthly_web',  # NON-discounted!
            price=4.99
        )
        SubscriptionService.process_webhook_event(test_user, event)

        # NO redemption should be created
        redemption = db_session.query(PromoRedemption).filter_by(user_id=test_user.id).first()
        assert redemption is None, "Redemption should NOT be created for non-discounted purchase"

        # promo_code_used should NOT be set
        assert test_user.promo_code_used is None, "promo_code_used should NOT be set"

    def test_attribution_clears_pending_code_after_non_discounted(self, app_context, db_session, test_user, valid_promo_code):
        """
        BUG FIX: pending_promo_code is cleared even for non-discounted purchase.
        """
        test_user.pending_promo_code = valid_promo_code.code
        db_session.commit()

        event = make_event(
            'INITIAL_PURCHASE',
            product_id='attuned_monthly_web',  # NON-discounted
            price=4.99
        )
        SubscriptionService.process_webhook_event(test_user, event)

        # pending_promo_code should be cleared
        assert test_user.pending_promo_code is None

    def test_attribution_sets_promo_code_used_for_discounted(self, app_context, db_session, test_user, valid_promo_code):
        """
        BUG FIX: promo_code_used is set ONLY for discounted purchases.
        """
        test_user.pending_promo_code = valid_promo_code.code
        db_session.commit()

        event = make_event(
            'INITIAL_PURCHASE',
            product_id='attuned_annual_web_discounted',  # DISCOUNTED
            price=23.99
        )
        SubscriptionService.process_webhook_event(test_user, event)

        assert test_user.promo_code_used == valid_promo_code.code

    def test_attribution_increments_redemption_count_only_for_discounted(self, app_context, db_session, test_user, valid_promo_code):
        """Redemption count only incremented for actual discounted purchases."""
        initial_count = valid_promo_code.redemption_count or 0
        test_user.pending_promo_code = valid_promo_code.code
        db_session.commit()

        # Purchase discounted product
        event = make_event(
            'INITIAL_PURCHASE',
            product_id='attuned_monthly_web_discounted',
            price=3.99
        )
        SubscriptionService.process_webhook_event(test_user, event)

        # Re-query the promo code to get updated count (session may have different object)
        updated_promo = db_session.query(PromoCode).filter_by(id=valid_promo_code.id).first()
        assert updated_promo.redemption_count == initial_count + 1

    def test_attribution_does_not_increment_count_for_non_discounted(self, app_context, db_session, test_user, valid_promo_code):
        """
        BUG FIX: Redemption count NOT incremented for non-discounted purchases.
        """
        initial_count = valid_promo_code.redemption_count or 0
        test_user.pending_promo_code = valid_promo_code.code
        db_session.commit()

        # Purchase NON-discounted product
        event = make_event(
            'INITIAL_PURCHASE',
            product_id='attuned_monthly_web',  # NON-discounted
            price=4.99
        )
        SubscriptionService.process_webhook_event(test_user, event)

        db_session.refresh(valid_promo_code)
        assert valid_promo_code.redemption_count == initial_count, "Count should not change"


# =============================================================================
# TestWebhookPromoIntegration - Full flow integration tests
# =============================================================================

class TestWebhookPromoIntegration:
    """Integration tests for webhook + promo validation flow."""

    def test_initial_purchase_discounted_records_redemption(self, app_context, db_session, test_user, valid_promo_code):
        """Full flow: validate -> purchase discounted -> redemption recorded."""
        # Step 1: Simulate validation (sets pending_promo_code)
        test_user.pending_promo_code = valid_promo_code.code
        db_session.commit()

        # Step 2: Webhook for discounted purchase
        event = make_event(
            'INITIAL_PURCHASE',
            product_id='attuned_monthly_web_discounted',
            price=3.99,
            store='STRIPE'
        )
        result = SubscriptionService.process_webhook_event(test_user, event)

        assert result['handled'] is True
        assert test_user.subscription_tier == 'premium'

        # Redemption should exist
        redemption = db_session.query(PromoRedemption).filter_by(user_id=test_user.id).first()
        assert redemption is not None

    def test_initial_purchase_non_discounted_no_redemption(self, app_context, db_session, test_user, valid_promo_code):
        """Full flow: validate -> purchase non-discounted -> NO redemption."""
        # Step 1: Simulate validation
        test_user.pending_promo_code = valid_promo_code.code
        db_session.commit()

        # Step 2: Webhook for NON-discounted purchase
        event = make_event(
            'INITIAL_PURCHASE',
            product_id='attuned_monthly_web',  # Full price
            price=4.99,
            store='STRIPE'
        )
        result = SubscriptionService.process_webhook_event(test_user, event)

        assert result['handled'] is True
        assert test_user.subscription_tier == 'premium'

        # NO redemption should exist
        redemption = db_session.query(PromoRedemption).filter_by(user_id=test_user.id).first()
        assert redemption is None

    def test_user_can_revalidate_after_non_discounted_purchase(self, client, app_context, db_session, test_user, valid_promo_code):
        """
        BUG FIX: Full flow test - user who bought full price can revalidate.

        This is the exact scenario reported by users:
        1. User validates code
        2. User buys full-price product (doesn't use discount)
        3. User tries to validate same code again
        4. Should SUCCEED (they never got the discount)
        """
        # Step 1: Create redemption for non-discounted product (simulating past behavior)
        redemption = PromoRedemption(
            promo_code_id=valid_promo_code.id,
            user_id=test_user.id,
            subscription_product='attuned_monthly_web',  # NON-discounted
            discounted_price=4.99,
            redeemed_at=datetime.now(timezone.utc) - timedelta(days=30),
        )
        db_session.add(redemption)
        db_session.commit()

        # Step 2: User tries to validate again
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'TESTPROMO'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is True, f"User should be able to revalidate, got: {data}"

    def test_user_blocked_after_discounted_purchase(self, client, app_context, db_session, test_user, valid_promo_code):
        """
        BUG FIX: Full flow test - user who bought discounted is blocked.

        1. User validates code
        2. User buys discounted product (uses discount)
        3. User tries to validate same code again
        4. Should FAIL (they already got the discount)
        """
        # Step 1: Create redemption for DISCOUNTED product
        redemption = PromoRedemption(
            promo_code_id=valid_promo_code.id,
            user_id=test_user.id,
            subscription_product='attuned_monthly_web_discounted',  # DISCOUNTED
            discounted_price=3.99,
            redeemed_at=datetime.now(timezone.utc) - timedelta(days=30),
        )
        db_session.add(redemption)
        db_session.commit()

        # Step 2: User tries to validate again
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(test_user.id)}

            response = client.post(
                '/api/promo/validate',
                headers={'Authorization': 'Bearer valid-token'},
                json={'code': 'TESTPROMO'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['valid'] is False, f"User should be blocked, got: {data}"
            assert data['error'] == 'Code already used'
