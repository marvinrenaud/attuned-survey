"""Promo code validation and management routes."""
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from ..extensions import db
from ..models.user import User
from ..models.promo_code import PromoCode
from ..models.promo_redemption import PromoRedemption
from ..middleware.auth import token_required
import logging

logger = logging.getLogger(__name__)

promo_bp = Blueprint('promo', __name__, url_prefix='/api/promo')


@promo_bp.route('/validate', methods=['POST'])
@token_required
def validate_promo_code(current_user_id):
    """
    Validate a promo code and associate with user.
    Returns offering_id for RevenueCat if valid.

    Sets user.pending_promo_code on success - this is cleared
    when the purchase webhook arrives and creates a promo_redemption.
    """
    try:
        data = request.get_json() or {}
        code = data.get('code', '').strip()

        if not code:
            return jsonify({'error': 'Code is required'}), 400

        # Normalize code for lookup (case-insensitive)
        code_upper = code.upper()

        # Find the code with influencer info
        promo = PromoCode.query.filter(
            func.upper(PromoCode.code) == code_upper
        ).first()

        if not promo:
            return jsonify({
                'valid': False,
                'error': 'Code not found'
            }), 200

        # Check code's own validity (active, not expired, under max)
        is_valid, error = promo.is_valid()
        if not is_valid:
            return jsonify({
                'valid': False,
                'error': error
            }), 200

        # Check if user already redeemed this code for a DISCOUNTED product
        # Users who validated but bought full-price can re-use the code
        existing = PromoRedemption.query.filter_by(
            user_id=current_user_id,
            promo_code_id=promo.id
        ).first()

        if existing:
            # Only block if they actually got the discount (bought a discounted product)
            product = existing.subscription_product or ''
            if 'discounted' in product.lower():
                return jsonify({
                    'valid': False,
                    'error': 'Code already used'
                }), 200
            # Otherwise, allow re-validation (they paid full price last time)

        # Get user and associate pending promo code
        user = db.session.get(User, current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user.pending_promo_code = promo.code
        db.session.commit()

        # Return validation success with offering info
        return jsonify({
            'valid': True,
            'code': promo.code,
            'discount_percent': promo.discount_percent,
            'influencer_name': promo.influencer.name if promo.influencer else None,
            'offering_id': promo.revenuecat_offering_id
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Promo validation failed: {str(e)}")
        return jsonify({'error': 'Validation failed'}), 500
