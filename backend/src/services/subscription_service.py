"""
Subscription service - handles RevenueCat webhook event processing.

This service encapsulates all subscription lifecycle logic:
- Processing webhook events (purchase, renewal, cancellation, etc.)
- Promo code attribution on purchase
- Store name mapping
"""
from datetime import datetime, timezone
import logging
from ..extensions import db
from ..models.user import User
from ..models.promo_code import PromoCode
from ..models.promo_redemption import PromoRedemption

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Handles RevenueCat webhook event processing."""

    # Map RevenueCat store values to our platform names
    STORE_MAP = {
        'APP_STORE': 'apple',
        'PLAY_STORE': 'google',
        'STRIPE': 'stripe',
        'AMAZON': 'amazon',
        'PROMOTIONAL': 'promo'
    }

    @classmethod
    def process_webhook_event(cls, user: User, event: dict) -> dict:
        """
        Process a RevenueCat webhook event.
        Returns dict with processing result.
        """
        event_type = event.get('type')

        handlers = {
            'INITIAL_PURCHASE': cls._handle_initial_purchase,
            'RENEWAL': cls._handle_renewal,
            'CANCELLATION': cls._handle_cancellation,
            'UNCANCELLATION': cls._handle_uncancellation,
            'EXPIRATION': cls._handle_expiration,
            'BILLING_ISSUE': cls._handle_billing_issue,
            'PRODUCT_CHANGE': cls._handle_product_change,
            'SUBSCRIBER_ALIAS': cls._handle_subscriber_alias,
        }

        handler = handlers.get(event_type)
        if not handler:
            logger.info(f"Unhandled event type: {event_type}")
            return {'handled': False, 'reason': 'unknown_event_type'}

        return handler(user, event)

    @classmethod
    def _handle_initial_purchase(cls, user: User, event: dict) -> dict:
        """New subscription purchase."""
        # Idempotency: check if already premium with same product
        product_id = event.get('product_id')
        if (user.subscription_tier == 'premium' and
                user.subscription_product_id == product_id):
            logger.info(f"Duplicate INITIAL_PURCHASE for user {user.id}, skipping")
            return {'handled': True, 'skipped': True}

        # Process pending promo code attribution FIRST (before modifying user)
        # This queries the database, so do it before any state changes
        cls._process_promo_attribution(user, event)

        # Update subscription state
        user.subscription_tier = 'premium'
        user.subscription_product_id = product_id
        user.subscription_platform = cls.STORE_MAP.get(event.get('store'), 'unknown')
        user.subscription_expires_at = cls._parse_timestamp(event.get('expiration_at_ms'))
        user.revenuecat_app_user_id = event.get('app_user_id')

        # Clear any billing issues
        user.billing_issue_detected_at = None
        user.subscription_cancelled_at = None

        # Store Stripe customer ID if present
        if event.get('stripe_customer_id'):
            user.stripe_customer_id = event.get('stripe_customer_id')

        db.session.commit()
        logger.info(f"User {user.id} subscribed via {user.subscription_platform}")

        return {'handled': True, 'new_tier': 'premium'}

    @classmethod
    def _handle_renewal(cls, user: User, event: dict) -> dict:
        """Subscription renewed."""
        new_expiry = cls._parse_timestamp(event.get('expiration_at_ms'))

        # Idempotency: check if expiry already matches
        if user.subscription_expires_at == new_expiry:
            return {'handled': True, 'skipped': True}

        user.subscription_expires_at = new_expiry
        user.billing_issue_detected_at = None  # Clear any prior issues
        db.session.commit()

        logger.info(f"User {user.id} renewed until {new_expiry}")
        return {'handled': True}

    @classmethod
    def _handle_cancellation(cls, user: User, event: dict) -> dict:
        """User cancelled (still has access until expiry)."""
        if user.subscription_cancelled_at is not None:
            return {'handled': True, 'skipped': True}

        user.subscription_cancelled_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.info(f"User {user.id} cancelled, access until {user.subscription_expires_at}")
        return {'handled': True}

    @classmethod
    def _handle_uncancellation(cls, user: User, event: dict) -> dict:
        """User re-enabled auto-renew."""
        user.subscription_cancelled_at = None
        db.session.commit()

        logger.info(f"User {user.id} uncancelled")
        return {'handled': True}

    @classmethod
    def _handle_expiration(cls, user: User, event: dict) -> dict:
        """Subscription expired - downgrade to free."""
        if user.subscription_tier == 'free':
            return {'handled': True, 'skipped': True}

        user.subscription_tier = 'free'
        user.subscription_cancelled_at = None
        user.billing_issue_detected_at = None
        # Keep historical fields: platform, product_id, expires_at
        db.session.commit()

        logger.info(f"User {user.id} expired, downgraded to free")
        return {'handled': True, 'new_tier': 'free'}

    @classmethod
    def _handle_billing_issue(cls, user: User, event: dict) -> dict:
        """Payment failed - flag for follow-up."""
        if user.billing_issue_detected_at is not None:
            return {'handled': True, 'skipped': True}

        user.billing_issue_detected_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.warning(f"User {user.id} has billing issue")
        return {'handled': True}

    @classmethod
    def _handle_product_change(cls, user: User, event: dict) -> dict:
        """User changed plans (e.g., monthly to annual)."""
        user.subscription_product_id = event.get('product_id')
        user.subscription_expires_at = cls._parse_timestamp(event.get('expiration_at_ms'))
        db.session.commit()

        logger.info(f"User {user.id} changed to product {user.subscription_product_id}")
        return {'handled': True}

    @classmethod
    def _handle_subscriber_alias(cls, user: User, event: dict) -> dict:
        """Link RevenueCat user ID (usually already matches)."""
        user.revenuecat_app_user_id = event.get('app_user_id')
        db.session.commit()
        return {'handled': True}

    @classmethod
    def _process_promo_attribution(cls, user: User, event: dict) -> None:
        """
        If user has pending promo code, record the redemption.
        Called during INITIAL_PURCHASE processing.
        """
        if not user.pending_promo_code:
            return

        # Get the session from the user's object state to maintain context
        from sqlalchemy.orm import object_session
        session = object_session(user)
        if session is None:
            session = db.session

        promo = session.query(PromoCode).filter(
            PromoCode.code == user.pending_promo_code
        ).first()

        if not promo:
            logger.warning(f"Pending promo code {user.pending_promo_code} not found")
            user.pending_promo_code = None
            return

        # Create redemption record
        redemption = PromoRedemption(
            promo_code_id=promo.id,
            user_id=user.id,
            subscription_product=event.get('product_id'),
            original_price=None,  # Unknown from webhook
            discounted_price=event.get('price')  # Actual amount paid
        )
        session.add(redemption)

        # Update promo code stats
        promo.redemption_count = (promo.redemption_count or 0) + 1

        # Move from pending to permanent
        user.promo_code_used = user.pending_promo_code
        user.pending_promo_code = None

        logger.info(f"User {user.id} redeemed promo {promo.code}")

    @staticmethod
    def _parse_timestamp(ms: int) -> datetime:
        """Convert milliseconds timestamp to datetime."""
        if not ms:
            return None
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
