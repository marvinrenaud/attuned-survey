"""Authentication routes for Supabase Auth integration."""
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from ..extensions import db, limiter
from ..models.user import User
from ..models.profile import Profile
from ..models.survey import SurveySubmission

from ..middleware.auth import token_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per hour")
def register_user():
    """
    Register a new user after Supabase Auth signup.
    
    Expected payload:
    {
        "id": "uuid-from-supabase-auth",
        "email": "user@example.com",
        "auth_provider": "email" | "google" | "apple" | "facebook",
        "display_name": "User Name",
        "demographics": {
            "gender": "man" | "woman" | "non-binary" | "rather_not_say",
            "sexual_orientation": "straight" | "gay" | "bisexual" | "rather_not_say",
            "relationship_structure": "monogamous" | "open" | "rather_not_say"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('id') or not data.get('email'):
            return jsonify({'error': 'Missing required fields: id, email'}), 400
        
        # Create user record
        user = User(
            id=data['id'],  # UUID from Supabase Auth
            email=data['email'],
            auth_provider=data.get('auth_provider', 'email'),
            display_name=data.get('display_name'),
            demographics=data.get('demographics', {}),
            subscription_tier='free',
            notification_preferences=data.get('notification_preferences', {}),
            onboarding_completed=False,
            last_login_at=datetime.utcnow()
        )
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"User registered: {user.email} ({user.id})")
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"User registration failed - duplicate: {str(e)}")
        return jsonify({'error': 'User already exists'}), 409
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"User registration failed: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
@token_required
def update_login(current_user_id):
    """
    Update last_login_at timestamp for existing user.
    """
    try:
        # User ID comes from token now, not body (security fix)
        user_id = current_user_id
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        user = User.query.filter_by(id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Login update failed: {str(e)}")
        return jsonify({'error': 'Login update failed'}), 500


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_user(current_user_id):
    """Get authenticated user details."""
    try:
        user = User.query.filter_by(id=current_user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get user failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user'}), 500


@auth_bp.route('/profile', methods=['PATCH'])
@token_required
def update_user(current_user_id):
    """
    Update authenticated user profile.
    
    Allowed updates:
    - display_name
    - demographics
    - notification_preferences
    - profile_sharing_setting
    - onboarding_completed
    """
    try:
        data = request.get_json()
        user = User.query.filter_by(id=current_user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update allowed fields
        if 'display_name' in data:
            user.display_name = data['display_name']
        
        if 'demographics' in data:
            user.demographics = data['demographics']
        
        if 'notification_preferences' in data:
            user.notification_preferences = data['notification_preferences']
        
        if 'profile_sharing_setting' in data:
            if data['profile_sharing_setting'] in ['all_responses', 'overlapping_only', 'demographics_only']:
                user.profile_sharing_setting = data['profile_sharing_setting']
        
        if 'onboarding_completed' in data:
            user.onboarding_completed = data['onboarding_completed']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"User update failed: {str(e)}")
        return jsonify({'error': 'Update failed'}), 500


@auth_bp.route('/profile', methods=['DELETE'])
@token_required
def delete_user(current_user_id):
    """
    Delete authenticated user account and all associated data.
    FR-81: Account deletion with cascade.
    """
    try:
        user = User.query.filter_by(id=current_user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Cascade delete will handle:
        # - profiles
        # - survey_progress
        # - sessions
        # - activity_history
        # - partner_connections
        # - remembered_partners
        # - push_notification_tokens
        # - subscription_transactions
        
        db.session.delete(user)
        db.session.commit()
        
        logger.info(f"User deleted: {current_user_id}")
        
        return jsonify({
            'success': True,
            'message': 'User account deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"User deletion failed: {str(e)}")
        return jsonify({'error': 'Deletion failed'}), 500


@auth_bp.route('/complete-demographics', methods=['POST'])
@token_required
def complete_demographics(current_user_id):
    """
    Mark demographics as complete (FR-04).
    
    Accepts EITHER boolean format (preferred) OR array format (backward compat).
    ...
    """
    try:
        data = request.get_json()
        
        # Validate name is present
        if 'name' not in data:
            return jsonify({'error': 'Missing required field: name'}), 400
        
        user = User.query.filter_by(id=current_user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update user name
        user.display_name = data['name']
        
        # Handle EITHER boolean format OR array format
        if 'has_penis' in data or 'likes_penis' in data:
            # New boolean format
            user.has_penis = data.get('has_penis', False)
            user.has_vagina = data.get('has_vagina', False)
            user.has_breasts = data.get('has_breasts', False)
            user.likes_penis = data.get('likes_penis', False)
            user.likes_vagina = data.get('likes_vagina', False)
            user.likes_breasts = data.get('likes_breasts', False)
            
        elif 'anatomy_self' in data or 'anatomy_preference' in data:
            # Old array format - convert to booleans
            anatomy_self = data.get('anatomy_self', [])
            anatomy_pref = data.get('anatomy_preference', [])
            
            user.has_penis = 'penis' in anatomy_self
            user.has_vagina = 'vagina' in anatomy_self
            user.has_breasts = 'breasts' in anatomy_self
            user.likes_penis = 'penis' in anatomy_pref
            user.likes_vagina = 'vagina' in anatomy_pref
            user.likes_breasts = 'breasts' in anatomy_pref
            
            # Also store in demographics for backward compat
            updated_demographics = {
                **user.demographics,
                'anatomy_self': anatomy_self,
                'anatomy_preference': anatomy_pref
            }
        else:
            return jsonify({'error': 'Missing anatomy fields (either booleans or arrays)'}), 400
        
        # Validate at least one "has" selected
        if not (user.has_penis or user.has_vagina or user.has_breasts):
            return jsonify({'error': 'Must select at least one anatomy option (what you have)'}), 400
        
        # Validate at least one "likes" selected
        if not (user.likes_penis or user.likes_vagina or user.likes_breasts):
            return jsonify({'error': 'Must select at least one anatomy preference (what you like)'}), 400
        
        # Build demographics object (merge with existing)
        updated_demographics = {
            **user.demographics,
            'anatomy_self': user.get_anatomy_self_array(),  # Keep in sync
            'anatomy_preference': user.get_anatomy_preference_array()
        }
        
        # Add optional demographics
        if 'gender' in data:
            updated_demographics['gender'] = data['gender']
        if 'sexual_orientation' in data:
            updated_demographics['sexual_orientation'] = data['sexual_orientation']
        if 'relationship_structure' in data:
            updated_demographics['relationship_structure'] = data['relationship_structure']
        
        user.demographics = updated_demographics
        user.profile_completed = True
        
        db.session.commit()
        
        # Check if this completes onboarding
        check_and_update_onboarding_status(user)
        
        logger.info(f"Profile completed for user: {user.email}")
        
        return jsonify({
            'success': True,
            'profile_completed': True,
            'onboarding_completed': user.onboarding_completed,
            'can_play': True,
            'has_personalization': user.onboarding_completed,
            # Return both formats for compatibility
            'anatomy': {
                'has_penis': user.has_penis,
                'has_vagina': user.has_vagina,
                'has_breasts': user.has_breasts,
                'likes_penis': user.likes_penis,
                'likes_vagina': user.likes_vagina,
                'likes_breasts': user.likes_breasts,
                'anatomy_self': user.get_anatomy_self_array(),
                'anatomy_preference': user.get_anatomy_preference_array()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Complete demographics failed: {str(e)}")
        return jsonify({'error': 'Failed to complete demographics'}), 500


@auth_bp.route('/validate-token', methods=['POST'])
def validate_token():
    """
    Validate Supabase JWT token and return user info.
    This would typically be done by Supabase middleware,
    but included here for completeness.
    """
    # In production, this would validate JWT signature
    # For now, return basic validation response
    return jsonify({
        'valid': True,
        'message': 'Token validation should be handled by Supabase Auth'
    }), 200


def check_and_update_onboarding_status(user):
    """
    Check if user has completed both profile (demographics) and survey.
    If so, set onboarding_completed = True.
    """
    # 1. Check Profile Completeness (managed by complete_demographics)
    if not user.profile_completed:
        return False
        
    # 2. Check Survey Completeness (SurveySubmission exists)
    submission = SurveySubmission.query.filter_by(user_id=user.id).first()
    if not submission:
        return False
        
    # Both complete -> Update status
    if not user.onboarding_completed:
        user.onboarding_completed = True
        db.session.commit()
        logger.info(f"Onboarding marked as complete for user: {user.id}")
        
    return True

