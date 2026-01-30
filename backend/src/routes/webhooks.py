"""RevenueCat webhook endpoint for subscription lifecycle events."""
import os
import logging
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.user import User
from ..services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/api/webhooks')


def verify_webhook_auth():
    """Verify Bearer token matches REVENUECAT_WEBHOOK_SECRET."""
    secret = os.environ.get('REVENUECAT_WEBHOOK_SECRET')
    if not secret:
        logger.warning("REVENUECAT_WEBHOOK_SECRET not configured")
        return False

    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False

    token = auth_header[7:]  # Remove 'Bearer ' prefix
    return token == secret


@webhooks_bp.route('/revenuecat', methods=['POST'])
def revenuecat_webhook():
    """
    POST /api/webhooks/revenuecat

    Handles subscription lifecycle events from RevenueCat.
    Uses Bearer token authentication (not HMAC signature).

    Events handled:
    - INITIAL_PURCHASE: New subscription
    - RENEWAL: Subscription renewed
    - CANCELLATION: User cancelled (still has access until expiry)
    - UNCANCELLATION: User re-enabled auto-renew
    - EXPIRATION: Subscription ended, revoke access
    - BILLING_ISSUE: Payment failed
    - PRODUCT_CHANGE: Plan upgrade/downgrade

    Always returns 200 to prevent RevenueCat from retrying.
    """
    # Verify authentication
    if not verify_webhook_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    event = data.get('event', {})

    app_user_id = event.get('app_user_id')
    event_type = event.get('type')
    event_id = event.get('id')

    logger.info(f"Webhook received: {event_type} for user {app_user_id}")

    if not app_user_id:
        logger.warning("Webhook missing app_user_id")
        return jsonify({'status': 'error', 'message': 'Missing app_user_id'}), 200

    # Look up user by UUID (app_user_id is typically the user's UUID)
    try:
        from uuid import UUID
        user_uuid = UUID(str(app_user_id))
        user = db.session.get(User, user_uuid)
    except (ValueError, TypeError):
        # Not a valid UUID, try by revenuecat_app_user_id field
        user = User.query.filter_by(revenuecat_app_user_id=app_user_id).first()

    if not user:
        logger.warning(f"User not found for app_user_id: {app_user_id}")
        # Return 200 to prevent retries - user may have been deleted
        return jsonify({'status': 'user_not_found', 'app_user_id': app_user_id}), 200

    # Process the event through subscription service
    try:
        result = SubscriptionService.process_webhook_event(user, event)

        logger.info(f"Webhook processed: {event_type} for user {user.id}, result: {result}")

        return jsonify({
            'status': 'processed',
            'event_id': event_id,
            **result
        }), 200

    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        db.session.rollback()
        # Still return 200 to prevent retries - log the error for investigation
        return jsonify({
            'status': 'error',
            'message': 'Processing failed',
            'event_id': event_id
        }), 200
