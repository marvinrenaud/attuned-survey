"""Subscription management and validation routes."""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timezone, timedelta
from ..extensions import db
from ..models.user import User
from ..middleware.auth import token_required
import logging

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

        user = User.query.filter_by(id=user_id).first()
        
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
def check_daily_limit(current_user_id, user_id):
    """
    Check if user has reached daily activity limit (FR-25).
    Free tier users have a daily limit.
    """
    try:
        # Authorization
        if str(current_user_id) != str(user_id):
            return jsonify({'error': 'Unauthorized'}), 403

        user = User.query.filter_by(id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Premium users have no limit
        if user.subscription_tier == 'premium':
            return jsonify({
                'has_limit': False,
                'limit_reached': False,
                'remaining': -1
            }), 200
        
        # Check if reset is needed
        if user.daily_activity_reset_at < datetime.now(timezone.utc) - timedelta(days=1):
            user.daily_activity_count = 0
            user.daily_activity_reset_at = datetime.now(timezone.utc)
            db.session.commit()
        
        daily_limit = 25  # FR-25: configurable limit
        limit_reached = user.daily_activity_count >= daily_limit
        
        return jsonify({
            'has_limit': True,
            'limit_reached': limit_reached,
            'count': user.daily_activity_count,
            'limit': daily_limit,
            'remaining': max(0, daily_limit - user.daily_activity_count)
        }), 200
        
    except Exception as e:
        logger.error(f"Check limit failed: {str(e)}")
        return jsonify({'error': 'Failed to check limit'}), 500


@subscriptions_bp.route('/increment-activity/<user_id>', methods=['POST'])
@token_required
def increment_activity_count(current_user_id, user_id):
    """
    Increment daily activity count for user.
    Called after each activity is presented.
    """

    try:
        # Authorization
        if str(current_user_id) != str(user_id):
            return jsonify({'error': 'Unauthorized'}), 403

        user = User.query.filter_by(id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Only increment for free tier
        if user.subscription_tier == 'free':
            user.daily_activity_count += 1
            db.session.commit()
        
        return jsonify({
            'success': True,
            'count': user.daily_activity_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Increment activity failed: {str(e)}")
        return jsonify({'error': 'Failed to increment'}), 500


@subscriptions_bp.route('/webhook/app-store', methods=['POST'])
def app_store_webhook():
    """
    Handle App Store subscription webhooks.
    Validates receipts and updates subscription status.
    """
    # TODO: Implement App Store receipt validation
    # This requires App Store Server API integration
    logger.info("App Store webhook received")
    return jsonify({'received': True}), 200


@subscriptions_bp.route('/webhook/play-store', methods=['POST'])
def play_store_webhook():
    """
    Handle Google Play Store subscription webhooks.
    Validates purchases and updates subscription status.
    """
    # TODO: Implement Play Store purchase validation
    # This requires Google Play Developer API integration
    logger.info("Play Store webhook received")
    return jsonify({'received': True}), 200
