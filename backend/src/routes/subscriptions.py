"""Subscription management and validation routes."""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timezone, timedelta
from ..extensions import db
from ..models.user import User
from ..middleware.auth import token_required
from ..services.config_service import get_config_int
import logging
import uuid

logger = logging.getLogger(__name__)

subscriptions_bp = Blueprint('subscriptions', __name__, url_prefix='/api/subscriptions')


@subscriptions_bp.route('/validate/<user_id>', methods=['GET'])
@token_required
def validate_subscription(current_user_id, user_id):
    """
    Validate user's subscription status (FR-26).
    Returns whether user has active premium subscription.
    """
    try:
        # Authorization
        if str(current_user_id) != str(user_id):
            return jsonify({'error': 'Unauthorized'}), 403

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
             return jsonify({'error': 'Invalid user ID'}), 400

        user = User.query.filter_by(id=uid).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        is_premium = (
            user.subscription_tier == 'premium' and
            (user.subscription_expires_at is None or user.subscription_expires_at > datetime.now(timezone.utc))
        )
        
        return jsonify({
            'user_id': str(user_id),
            'subscription_tier': user.subscription_tier,
            'is_premium': is_premium,
            'expires_at': user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            'daily_activity_count': user.daily_activity_count,
            'daily_activity_reset_at': user.daily_activity_reset_at.isoformat() if user.daily_activity_reset_at else None
        }), 200
        
    except Exception as e:
        logger.error(f"Subscription validation failed: {str(e)}")
        return jsonify({'error': 'Validation failed'}), 500


@subscriptions_bp.route('/check-limit/<user_id>', methods=['GET'])
@token_required
def check_activity_limit(current_user_id, user_id):
    """
    Check if user has reached lifetime activity limit.
    Free tier users have a configurable lifetime limit.
    """
    try:
        # Authorization
        if str(current_user_id) != str(user_id):
            return jsonify({'error': 'Unauthorized'}), 403

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return jsonify({'error': 'Invalid user ID'}), 400

        user = User.query.filter_by(id=uid).first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Premium users have no limit
        if user.subscription_tier == 'premium':
            return jsonify({
                'has_limit': False,
                'limit_reached': False,
                'remaining': -1
            }), 200

        # Get configurable limit from app_config
        limit = get_config_int('free_tier_activity_limit', 10)
        used = user.lifetime_activity_count or 0
        limit_reached = used >= limit

        return jsonify({
            'has_limit': True,
            'limit_reached': limit_reached,
            'activities_used': used,
            'limit': limit,
            'remaining': max(0, limit - used)
        }), 200

    except Exception as e:
        logger.error(f"Check limit failed: {str(e)}")
        return jsonify({'error': 'Failed to check limit'}), 500


@subscriptions_bp.route('/increment-activity/<user_id>', methods=['POST'])
@token_required
def increment_activity_count(current_user_id, user_id):
    """
    Increment lifetime activity count for user.
    Called after each activity is presented.
    Only increments for free tier users.
    """
    try:
        # Authorization
        if str(current_user_id) != str(user_id):
            return jsonify({'error': 'Unauthorized'}), 403

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return jsonify({'error': 'Invalid user ID'}), 400

        user = User.query.filter_by(id=uid).first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Only increment for free tier
        if user.subscription_tier == 'free':
            user.lifetime_activity_count = (user.lifetime_activity_count or 0) + 1
            db.session.commit()

        return jsonify({
            'success': True,
            'lifetime_activity_count': user.lifetime_activity_count or 0
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Increment activity failed: {str(e)}")
        return jsonify({'error': 'Failed to increment'}), 500


@subscriptions_bp.route('/status/<user_id>', methods=['GET'])
@token_required
def get_subscription_status(current_user_id, user_id):
    """
    Get enhanced subscription status with all relevant fields.
    """
    try:
        # Authorization
        if str(current_user_id) != str(user_id):
            return jsonify({'error': 'Unauthorized'}), 403

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return jsonify({'error': 'Invalid user ID'}), 400

        user = User.query.filter_by(id=uid).first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        limit = get_config_int('free_tier_activity_limit', 10)
        is_premium = (
            user.subscription_tier == 'premium' and
            (user.subscription_expires_at is None or
             user.subscription_expires_at > datetime.now(timezone.utc))
        )

        return jsonify({
            'user_id': str(user_id),
            'subscription_tier': user.subscription_tier,
            'is_premium': is_premium,
            'expires_at': user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            'is_cancelled': user.subscription_cancelled_at is not None and is_premium,
            'platform': user.subscription_platform,
            'product_id': user.subscription_product_id,
            'activities_used': user.lifetime_activity_count or 0,
            'activities_limit': limit if not is_premium else None,
            'activities_remaining': max(0, limit - (user.lifetime_activity_count or 0)) if not is_premium else None,
            'has_billing_issue': user.billing_issue_detected_at is not None,
            'promo_code_used': user.promo_code_used
        }), 200

    except Exception as e:
        logger.error(f"Get status failed: {str(e)}")
        return jsonify({'error': 'Failed to get status'}), 500


@subscriptions_bp.route('/pricing', methods=['GET'])
def get_pricing():
    """
    GET /api/subscriptions/pricing

    Returns subscription pricing for all plans.
    Public endpoint - no auth required.
    Prices are read from app_config for easy updates.
    """
    try:
        # Get prices from config (with defaults)
        monthly_price = float(get_config_int('monthly_price_usd', 499) / 100) if get_config_int('monthly_price_usd', 0) > 100 else 4.99
        annual_price = float(get_config_int('annual_price_usd', 2999) / 100) if get_config_int('annual_price_usd', 0) > 100 else 29.99
        discount_percent = get_config_int('promo_discount_percent', 20)

        # Try to get string values from app_config for prices
        from ..models.app_config import AppConfig
        monthly_config = AppConfig.query.filter_by(key='monthly_price_usd').first()
        annual_config = AppConfig.query.filter_by(key='annual_price_usd').first()

        if monthly_config and monthly_config.value:
            try:
                monthly_price = float(monthly_config.value)
            except ValueError:
                pass

        if annual_config and annual_config.value:
            try:
                annual_price = float(annual_config.value)
            except ValueError:
                pass

        # Calculate discounted prices
        discounted_monthly = round(monthly_price * (1 - discount_percent / 100), 2)
        discounted_annual = round(annual_price * (1 - discount_percent / 100), 2)
        monthly_equivalent = round(annual_price / 12, 2)

        return jsonify({
            'monthly': {
                'price': monthly_price,
                'price_display': f'${monthly_price:.2f}/month'
            },
            'annual': {
                'price': annual_price,
                'price_display': f'${annual_price:.2f}/year',
                'monthly_equivalent': monthly_equivalent
            },
            'discounted_monthly': {
                'price': discounted_monthly,
                'price_display': f'${discounted_monthly:.2f}/month',
                'original_price': monthly_price,
                'discount_percent': discount_percent
            },
            'discounted_annual': {
                'price': discounted_annual,
                'price_display': f'${discounted_annual:.2f}/year',
                'original_price': annual_price,
                'discount_percent': discount_percent
            }
        }), 200

    except Exception as e:
        logger.error(f"Get pricing failed: {str(e)}")
        return jsonify({'error': 'Failed to get pricing'}), 500
