"""
Tests for RevenueCat webhook endpoint.

TDD: These tests are written BEFORE implementation.
Tests the HTTP layer that wires up to SubscriptionService.
"""
import os
import pytest
import uuid
import hmac
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from src.models.user import User


@pytest.fixture
def app_context(app):
    """Ensure app context is pushed"""
    with app.app_context():
        yield


@pytest.fixture
def test_user(db_session):
    """Create a test user for webhook events."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f'webhook-{user_id.hex[:8]}@test.com',
        display_name='Webhook Test User',
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


def make_webhook_payload(event_type, user_id, **kwargs):
    """Helper to create RevenueCat webhook payloads."""
    default_expiration = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp() * 1000)
    return {
        'api_version': '1.0',
        'event': {
            'type': event_type,
            'id': f'evt_{uuid.uuid4().hex[:12]}',
            'app_user_id': str(user_id),
            'product_id': kwargs.get('product_id', 'attuned_monthly'),
            'expiration_at_ms': kwargs.get('expiration_at_ms', default_expiration),
            'store': kwargs.get('store', 'APP_STORE'),
            'price': kwargs.get('price', 4.99),
            'environment': 'PRODUCTION',
            **{k: v for k, v in kwargs.items() if k not in ['product_id', 'expiration_at_ms', 'store', 'price']}
        }
    }


class TestWebhookAuthentication:
    """Tests for webhook signature verification."""

    def test_webhook_rejects_missing_auth(self, client, app_context):
        """401 without Authorization header."""
        payload = make_webhook_payload('INITIAL_PURCHASE', uuid.uuid4())

        response = client.post(
            '/api/webhooks/revenuecat',
            json=payload
        )

        assert response.status_code == 401

    @patch.dict(os.environ, {"REVENUECAT_WEBHOOK_SECRET": "test-secret"})
    def test_webhook_rejects_invalid_auth(self, client, app_context):
        """401 with wrong secret."""
        payload = make_webhook_payload('INITIAL_PURCHASE', uuid.uuid4())

        response = client.post(
            '/api/webhooks/revenuecat',
            json=payload,
            headers={'Authorization': 'Bearer wrong-secret'}
        )

        assert response.status_code == 401

    @patch.dict(os.environ, {"REVENUECAT_WEBHOOK_SECRET": "test-secret"})
    def test_webhook_accepts_valid_auth(self, client, app_context, test_user, db_session):
        """200 with correct Bearer token."""
        payload = make_webhook_payload('INITIAL_PURCHASE', test_user.id)

        response = client.post(
            '/api/webhooks/revenuecat',
            json=payload,
            headers={'Authorization': 'Bearer test-secret'}
        )

        assert response.status_code == 200


class TestWebhookEventProcessing:
    """Tests for webhook event processing."""

    @patch.dict(os.environ, {"REVENUECAT_WEBHOOK_SECRET": "test-secret"})
    def test_initial_purchase_sets_premium(self, client, app_context, test_user, db_session):
        """INITIAL_PURCHASE -> subscription_tier='premium'"""
        payload = make_webhook_payload('INITIAL_PURCHASE', test_user.id, store='STRIPE')

        response = client.post(
            '/api/webhooks/revenuecat',
            json=payload,
            headers={'Authorization': 'Bearer test-secret'}
        )

        assert response.status_code == 200

        db_session.refresh(test_user)
        assert test_user.subscription_tier == 'premium'
        assert test_user.subscription_platform == 'stripe'

    @patch.dict(os.environ, {"REVENUECAT_WEBHOOK_SECRET": "test-secret"})
    def test_expiration_downgrades_to_free(self, client, app_context, test_user, db_session):
        """EXPIRATION -> subscription_tier='free'"""
        # First make user premium
        test_user.subscription_tier = 'premium'
        db_session.commit()

        payload = make_webhook_payload('EXPIRATION', test_user.id)

        response = client.post(
            '/api/webhooks/revenuecat',
            json=payload,
            headers={'Authorization': 'Bearer test-secret'}
        )

        assert response.status_code == 200

        db_session.refresh(test_user)
        assert test_user.subscription_tier == 'free'

    @patch.dict(os.environ, {"REVENUECAT_WEBHOOK_SECRET": "test-secret"})
    def test_unknown_user_returns_200(self, client, app_context):
        """Unknown app_user_id returns 200 (no retries)."""
        unknown_id = uuid.uuid4()
        payload = make_webhook_payload('INITIAL_PURCHASE', unknown_id)

        response = client.post(
            '/api/webhooks/revenuecat',
            json=payload,
            headers={'Authorization': 'Bearer test-secret'}
        )

        # Returns 200 to prevent RevenueCat from retrying
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'user_not_found'

    @patch.dict(os.environ, {"REVENUECAT_WEBHOOK_SECRET": "test-secret"})
    def test_unknown_event_type_returns_200(self, client, app_context, test_user, db_session):
        """Unhandled event type returns 200."""
        payload = make_webhook_payload('SOME_FUTURE_EVENT', test_user.id)

        response = client.post(
            '/api/webhooks/revenuecat',
            json=payload,
            headers={'Authorization': 'Bearer test-secret'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'processed'

    @patch.dict(os.environ, {"REVENUECAT_WEBHOOK_SECRET": "test-secret"})
    def test_cancellation_sets_timestamp(self, client, app_context, test_user, db_session):
        """CANCELLATION sets subscription_cancelled_at"""
        test_user.subscription_tier = 'premium'
        db_session.commit()

        payload = make_webhook_payload('CANCELLATION', test_user.id)

        response = client.post(
            '/api/webhooks/revenuecat',
            json=payload,
            headers={'Authorization': 'Bearer test-secret'}
        )

        assert response.status_code == 200

        db_session.refresh(test_user)
        assert test_user.subscription_cancelled_at is not None
        assert test_user.subscription_tier == 'premium'  # Still premium until expiry

    @patch.dict(os.environ, {"REVENUECAT_WEBHOOK_SECRET": "test-secret"})
    def test_billing_issue_sets_timestamp(self, client, app_context, test_user, db_session):
        """BILLING_ISSUE sets billing_issue_detected_at"""
        test_user.subscription_tier = 'premium'
        db_session.commit()

        payload = make_webhook_payload('BILLING_ISSUE', test_user.id)

        response = client.post(
            '/api/webhooks/revenuecat',
            json=payload,
            headers={'Authorization': 'Bearer test-secret'}
        )

        assert response.status_code == 200

        db_session.refresh(test_user)
        assert test_user.billing_issue_detected_at is not None
