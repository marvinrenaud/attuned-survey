"""Authentication routes for Supabase Auth integration."""
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from ..extensions import db
from ..models.user import User
from ..models.profile import Profile

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
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
        
        current_app.logger.info(f"User registered: {user.email} ({user.id})")
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"User registration failed - duplicate: {str(e)}")
        return jsonify({'error': 'User already exists'}), 409
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"User registration failed: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def update_login():
    """
    Update last_login_at timestamp for existing user.
    
    Expected payload:
    {
        "user_id": "uuid-from-supabase-auth"
    }
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
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
        current_app.logger.error(f"Login update failed: {str(e)}")
        return jsonify({'error': 'Login update failed'}), 500


@auth_bp.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user details by ID."""
    try:
        user = User.query.filter_by(id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user'}), 500


@auth_bp.route('/user/<user_id>', methods=['PATCH'])
def update_user(user_id):
    """
    Update user profile.
    
    Allowed updates:
    - display_name
    - demographics
    - notification_preferences
    - profile_sharing_setting
    - onboarding_completed
    """
    try:
        data = request.get_json()
        user = User.query.filter_by(id=user_id).first()
        
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
        current_app.logger.error(f"User update failed: {str(e)}")
        return jsonify({'error': 'Update failed'}), 500


@auth_bp.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete user account and all associated data.
    FR-81: Account deletion with cascade.
    """
    try:
        user = User.query.filter_by(id=user_id).first()
        
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
        
        current_app.logger.info(f"User deleted: {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'User account deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"User deletion failed: {str(e)}")
        return jsonify({'error': 'Deletion failed'}), 500


@auth_bp.route('/user/<user_id>/complete-demographics', methods=['POST'])
def complete_demographics(user_id):
    """
    Mark demographics as complete (FR-04).
    Required fields: name, anatomy_self, anatomy_preference
    
    This gates game access - users must complete demographics before playing.
    
    Expected payload:
    {
        "name": "Display Name",
        "anatomy_self": ["penis", "vagina", "breasts"],
        "anatomy_preference": ["penis", "vagina", "breasts"],
        "gender": "woman" (optional),
        "sexual_orientation": "bisexual" (optional),
        "relationship_structure": "open" (optional)
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'anatomy_self', 'anatomy_preference']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Validate anatomy is array
        if not isinstance(data['anatomy_self'], list) or not isinstance(data['anatomy_preference'], list):
            return jsonify({'error': 'anatomy_self and anatomy_preference must be arrays'}), 400
        
        user = User.query.filter_by(id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update user with demographics
        user.display_name = data['name']
        
        # Build demographics object (merge with existing)
        updated_demographics = {
            **user.demographics,
            'anatomy_self': data['anatomy_self'],
            'anatomy_preference': data['anatomy_preference']
        }
        
        # Add optional demographics
        if 'gender' in data:
            updated_demographics['gender'] = data['gender']
        if 'sexual_orientation' in data:
            updated_demographics['sexual_orientation'] = data['sexual_orientation']
        if 'relationship_structure' in data:
            updated_demographics['relationship_structure'] = data['relationship_structure']
        
        user.demographics = updated_demographics
        user.demographics_completed = True
        
        db.session.commit()
        
        current_app.logger.info(f"Demographics completed for user: {user.email}")
        
        return jsonify({
            'success': True,
            'demographics_completed': True,
            'onboarding_completed': user.onboarding_completed,
            'can_play': True,
            'has_personalization': user.onboarding_completed
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Complete demographics failed: {str(e)}")
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

