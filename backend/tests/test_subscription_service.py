"""
Unit tests for SubscriptionService - tests webhook event handlers directly.

TDD: These tests are written BEFORE implementation.
These tests operate on the service layer without HTTP, testing handlers
directly with mock User objects.
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

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
def free_user(db_session):
    """Free tier user for testing."""
    user = User(
        id=uuid.uuid4(),
        email=f'free-{uuid.uuid4().hex[:8]}@test.com',
        display_name='Free User',
        auth_provider='email',
        demographics={},
        subscription_tier='free',
        lifetime_activity_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def premium_user(db_session):
    """Premium user with future expiry."""
    user = User(
        id=uuid.uuid4(),
        email=f'premium-{uuid.uuid4().hex[:8]}@test.com',
        display_name='Premium User',
        auth_provider='email',
        demographics={},
        subscription_tier='premium',
        subscription_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        subscription_product_id='attuned_monthly',
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def cancelled_user(db_session):
    """Premium user who cancelled but still has access."""
    user = User(
        id=uuid.uuid4(),
        email=f'cancelled-{uuid.uuid4().hex[:8]}@test.com',
        display_name='Cancelled User',
        auth_provider='email',
        demographics={},
        subscription_tier='premium',
        subscription_expires_at=datetime.now(timezone.utc) + timedelta(days=15),
        subscription_cancelled_at=datetime.now(timezone.utc) - timedelta(days=5),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def user_with_billing_issue(db_session):
    """Premium user with billing problem."""
    user = User(
        id=uuid.uuid4(),
        email=f'billing-{uuid.uuid4().hex[:8]}@test.com',
        display_name='Billing Issue User',
        auth_provider='email',
        demographics={},
        subscription_tier='premium',
        billing_issue_detected_at=datetime.now(timezone.utc) - timedelta(days=2),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def valid_promo_code(db_session):
    """Active promo code for testing."""
    influencer = Influencer(
        name='Test Influencer',
        email='test@influencer.com',
        platform='instagram',
        status='active',
    )
    db_session.add(influencer)
    db_session.flush()

    code = PromoCode(
        influencer_id=influencer.id,
        code='TESTCODE',
        discount_percent=20,
        revenuecat_offering_id='discounted_20_percent',
        is_active=True,
        redemption_count=0,
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


class TestInitialPurchaseHandler:
    """Tests for INITIAL_PURCHASE event handler."""

    def test_handle_initial_purchase_sets_premium(self, app_context, db_session, free_user):
        """User upgraded to premium with correct fields."""
        from src.services.subscription_service import SubscriptionService

        event = make_event('INITIAL_PURCHASE', product_id='attuned_monthly', store='STRIPE')
        result = SubscriptionService.process_webhook_event(free_user, event)

        assert result['handled'] is True
        assert free_user.subscription_tier == 'premium'
        assert free_user.subscription_platform == 'stripe'
        assert free_user.subscription_product_id == 'attuned_monthly'

    def test_handle_initial_purchase_idempotent(self, app_context, db_session, premium_user):
        """Duplicate purchase event is skipped."""
        from src.services.subscription_service import SubscriptionService

        event = make_event('INITIAL_PURCHASE', product_id='attuned_monthly')
        result = SubscriptionService.process_webhook_event(premium_user, event)

        assert result['skipped'] is True

    def test_handle_initial_purchase_clears_billing_issue(self, app_context, db_session, user_with_billing_issue):
        """Successful purchase clears prior billing issue."""
        from src.services.subscription_service import SubscriptionService

        event = make_event('INITIAL_PURCHASE')
        SubscriptionService.process_webhook_event(user_with_billing_issue, event)

        assert user_with_billing_issue.billing_issue_detected_at is None

    def test_handle_initial_purchase_with_pending_promo(self, app_context, db_session, free_user, valid_promo_code):
        """Pending promo code creates redemption record when purchasing DISCOUNTED product."""
        from src.services.subscription_service import SubscriptionService

        free_user.pending_promo_code = valid_promo_code.code
        db_session.commit()

        # Must purchase a discounted product for redemption to be recorded
        event = make_event('INITIAL_PURCHASE', product_id='attuned_monthly_discounted', price=3.99)
        SubscriptionService.process_webhook_event(free_user, event)

        assert free_user.promo_code_used == valid_promo_code.code
        assert free_user.pending_promo_code is None

        # Re-query the promo code to get updated redemption_count
        updated_promo = db_session.query(PromoCode).filter_by(id=valid_promo_code.id).first()
        assert updated_promo.redemption_count == 1

        redemption = db_session.query(PromoRedemption).filter_by(user_id=free_user.id).first()
        assert redemption is not None
        assert float(redemption.discounted_price) == 3.99

    def test_handle_initial_purchase_without_promo(self, app_context, db_session, free_user):
        """No pending promo code creates no redemption."""
        from src.services.subscription_service import SubscriptionService

        free_user.pending_promo_code = None
        db_session.commit()

        event = make_event('INITIAL_PURCHASE')
        SubscriptionService.process_webhook_event(free_user, event)

        redemption = db_session.query(PromoRedemption).filter_by(user_id=free_user.id).first()
        assert redemption is None

    def test_handle_initial_purchase_stores_stripe_customer_id(self, app_context, db_session, free_user):
        """Stripe customer ID stored if present in event."""
        from src.services.subscription_service import SubscriptionService

        event = make_event('INITIAL_PURCHASE', stripe_customer_id='cus_abc123')
        SubscriptionService.process_webhook_event(free_user, event)

        assert free_user.stripe_customer_id == 'cus_abc123'


class TestRenewalHandler:
    """Tests for RENEWAL event handler."""

    def test_handle_renewal_extends_expiry(self, app_context, db_session, premium_user):
        """Renewal updates expiration date."""
        from src.services.subscription_service import SubscriptionService

        # Make old_expiry timezone-aware for comparison
        old_expiry = premium_user.subscription_expires_at
        if old_expiry.tzinfo is None:
            old_expiry = old_expiry.replace(tzinfo=timezone.utc)

        new_expiry_ms = int((datetime.now(timezone.utc) + timedelta(days=60)).timestamp() * 1000)

        event = make_event('RENEWAL', expiration_at_ms=new_expiry_ms)
        SubscriptionService.process_webhook_event(premium_user, event)

        new_expiry = premium_user.subscription_expires_at
        if new_expiry.tzinfo is None:
            new_expiry = new_expiry.replace(tzinfo=timezone.utc)

        assert new_expiry > old_expiry

    def test_handle_renewal_clears_billing_issue(self, app_context, db_session, user_with_billing_issue):
        """Successful renewal clears billing issue."""
        from src.services.subscription_service import SubscriptionService

        event = make_event('RENEWAL')
        SubscriptionService.process_webhook_event(user_with_billing_issue, event)

        assert user_with_billing_issue.billing_issue_detected_at is None


class TestCancellationHandler:
    """Tests for CANCELLATION event handler."""

    def test_handle_cancellation_sets_timestamp(self, app_context, db_session, premium_user):
        """Cancellation records timestamp."""
        from src.services.subscription_service import SubscriptionService

        assert premium_user.subscription_cancelled_at is None

        event = make_event('CANCELLATION')
        SubscriptionService.process_webhook_event(premium_user, event)

        assert premium_user.subscription_cancelled_at is not None
        assert premium_user.subscription_tier == 'premium'  # Still premium until expiry

    def test_handle_cancellation_idempotent(self, app_context, db_session, cancelled_user):
        """Duplicate cancellation is skipped."""
        from src.services.subscription_service import SubscriptionService

        original_ts = cancelled_user.subscription_cancelled_at

        event = make_event('CANCELLATION')
        result = SubscriptionService.process_webhook_event(cancelled_user, event)

        assert result['skipped'] is True
        assert cancelled_user.subscription_cancelled_at == original_ts


class TestUncancellationHandler:
    """Tests for UNCANCELLATION event handler."""

    def test_handle_uncancellation_clears_timestamp(self, app_context, db_session, cancelled_user):
        """Uncancellation clears cancelled timestamp."""
        from src.services.subscription_service import SubscriptionService

        event = make_event('UNCANCELLATION')
        SubscriptionService.process_webhook_event(cancelled_user, event)

        assert cancelled_user.subscription_cancelled_at is None


class TestExpirationHandler:
    """Tests for EXPIRATION event handler."""

    def test_handle_expiration_downgrades_to_free(self, app_context, db_session, premium_user):
        """Expiration downgrades user to free tier."""
        from src.services.subscription_service import SubscriptionService

        event = make_event('EXPIRATION')
        SubscriptionService.process_webhook_event(premium_user, event)

        assert premium_user.subscription_tier == 'free'

    def test_handle_expiration_idempotent(self, app_context, db_session, free_user):
        """Already-free user is skipped."""
        from src.services.subscription_service import SubscriptionService

        event = make_event('EXPIRATION')
        result = SubscriptionService.process_webhook_event(free_user, event)

        assert result['skipped'] is True


class TestBillingIssueHandler:
    """Tests for BILLING_ISSUE event handler."""

    def test_handle_billing_issue_sets_timestamp(self, app_context, db_session, premium_user):
        """Billing issue records timestamp."""
        from src.services.subscription_service import SubscriptionService

        event = make_event('BILLING_ISSUE')
        SubscriptionService.process_webhook_event(premium_user, event)

        assert premium_user.billing_issue_detected_at is not None


class TestProductChangeHandler:
    """Tests for PRODUCT_CHANGE event handler."""

    def test_handle_product_change_updates_product(self, app_context, db_session, premium_user):
        """Product change updates product ID."""
        from src.services.subscription_service import SubscriptionService

        premium_user.subscription_product_id = 'attuned_monthly'
        db_session.commit()

        event = make_event('PRODUCT_CHANGE', product_id='attuned_annual')
        SubscriptionService.process_webhook_event(premium_user, event)

        assert premium_user.subscription_product_id == 'attuned_annual'


class TestUnknownEvents:
    """Tests for unknown event types."""

    def test_unknown_event_type_not_handled(self, app_context, db_session, free_user):
        """Unknown event type returns handled=False."""
        from src.services.subscription_service import SubscriptionService

        event = make_event('SOME_FUTURE_EVENT')
        result = SubscriptionService.process_webhook_event(free_user, event)

        assert result['handled'] is False


class TestStoreMapping:
    """Tests for store name mapping."""

    def test_store_mapping(self, app_context, db_session, free_user):
        """Store names mapped correctly."""
        from src.services.subscription_service import SubscriptionService

        test_cases = [
            ('APP_STORE', 'apple'),
            ('PLAY_STORE', 'google'),
            ('STRIPE', 'stripe'),
        ]

        for rc_store, expected in test_cases:
            # Reset user
            free_user.subscription_tier = 'free'
            free_user.subscription_product_id = None
            db_session.commit()

            event = make_event('INITIAL_PURCHASE', store=rc_store)
            SubscriptionService.process_webhook_event(free_user, event)

            assert free_user.subscription_platform == expected, f"Expected {expected} for {rc_store}"
