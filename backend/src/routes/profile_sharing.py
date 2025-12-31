"""Profile sharing and visibility routes."""
from flask import Blueprint, jsonify, request, current_app

from ..extensions import db
from ..models.user import User
from ..models.profile import Profile
from ..middleware.auth import token_required
import logging
import uuid

logger = logging.getLogger(__name__)

profile_sharing_bp = Blueprint('profile_sharing', __name__, url_prefix='/api/profile-sharing')


@profile_sharing_bp.route('/settings', methods=['GET'])
@token_required
def get_sharing_settings(current_user_id):
    """
    Get user's profile sharing settings (FR-62).
    """
    try:
        try:
            user_uuid = uuid.UUID(current_user_id)
        except ValueError:
            return jsonify({'error': 'Invalid User ID token'}), 400

        user = User.query.filter_by(id=user_uuid).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user_id': str(user_uuid),
            'profile_sharing_setting': user.profile_sharing_setting
        }), 200
        
    except Exception as e:
        logger.error(f"Get sharing settings failed: {str(e)}")
        return jsonify({'error': 'Failed to get settings'}), 500


@profile_sharing_bp.route('/settings', methods=['PUT'])
@token_required
def update_sharing_settings(current_user_id):
    """
    Update user's profile sharing settings (FR-73).
    
    Expected payload:
    {
        "profile_sharing_setting": "all_responses" | "overlapping_only" | "demographics_only"
    }
    """
    try:
        try:
            user_uuid = uuid.UUID(current_user_id)
        except ValueError:
            return jsonify({'error': 'Invalid User ID token'}), 400

        data = request.get_json()
        setting = data.get('profile_sharing_setting')
        
        if setting not in ['all_responses', 'overlapping_only', 'demographics_only']:
            return jsonify({'error': 'Invalid sharing setting'}), 400
        
        user = User.query.filter_by(id=user_uuid).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.profile_sharing_setting = setting
        db.session.commit()
        
        return jsonify({
            'success': True,
            'profile_sharing_setting': setting
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update sharing settings failed: {str(e)}")
        return jsonify({'error': 'Failed to update settings'}), 500


@profile_sharing_bp.route('/partner-profile/<partner_id>', methods=['GET'])
@token_required
def get_partner_profile(current_user_id, partner_id):
    """
    Get partner's profile based on their sharing settings (FR-69, FR-70, FR-71).
    Returns filtered profile data according to partner's preferences.
    """
    try:
        try:
            requester_uuid = uuid.UUID(current_user_id)
            partner_uuid = uuid.UUID(partner_id)
        except ValueError:
            return jsonify({'error': 'Invalid User ID formatted'}), 400

        # Get partner's user and profile
        partner = User.query.filter_by(id=partner_uuid).first()
        
        if not partner:
            return jsonify({'error': 'Partner not found'}), 404
        
        partner_profile = Profile.query.filter_by(user_id=partner_uuid).first()
        
        if not partner_profile:
            return jsonify({'error': 'Partner profile not found'}), 404
        
        # Get sharing setting
        sharing_setting = partner.profile_sharing_setting
        
        # Base response with demographics
        response = {
            'user_id': str(partner_id),
            'display_name': partner.display_name,
            'demographics': partner.demographics,
            'sharing_setting': sharing_setting
        }
        
        # FR-71: Demographics only
        if sharing_setting == 'demographics_only':
            return jsonify(response), 200
        
        # FR-69: All responses
        if sharing_setting == 'all_responses':
            response['profile'] = partner_profile.to_dict()
            return jsonify(response), 200
        
        # FR-70: Overlapping only
        if sharing_setting == 'overlapping_only':
            requester_profile = Profile.query.filter_by(user_id=requester_uuid).first()
            
            if not requester_profile:
                # Can't determine overlap without requester profile
                response['profile'] = None
                return jsonify(response), 200
            
            # Filter to overlapping activities
            # (Both parties answered 3+ on Likert scale or 0.5+ on normalized)
            overlapping_activities = {}
            
            for key, value in partner_profile.activities.items():
                if key in requester_profile.activities:
                    if float(value) >= 0.5 and float(requester_profile.activities[key]) >= 0.5:
                        overlapping_activities[key] = value
            
            response['profile'] = {
                'activities': overlapping_activities,
                'overlapping_count': len(overlapping_activities)
            }
            return jsonify(response), 200
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Get partner profile failed: {str(e)}")
        return jsonify({'error': 'Failed to get partner profile'}), 500

