from flask import Blueprint, jsonify, request, current_app
from ..extensions import db
from ..models.notification import PushNotificationToken
from ..models.user import User
from ..models.user import User
from ..middleware.auth import token_required
import logging
import uuid

logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/register', methods=['POST'])
@token_required
def register_token(current_user_id):
    """
    Register a device token for push notifications (FR-75).
    
    Expected payload:
    {
        "user_id": "uuid",
        "device_token": "fcm-or-apns-token",
        "platform": "ios" | "android"
    }
    """
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        device_token = data.get('device_token')
        platform = data.get('platform')
        
        if not all([user_id, device_token, platform]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        if platform not in ['ios', 'android']:
            return jsonify({'error': 'Invalid platform'}), 400
            
        if str(current_user_id) != str(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Verify user exists (Cast to UUID for query)
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
             return jsonify({'error': 'Invalid User ID'}), 400
             
        user = User.query.filter_by(id=user_uuid).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Check if token already exists
        token = PushNotificationToken.query.filter_by(device_token=device_token).first()
        
        if token:
            # Update user_id if changed (e.g. user logged in on same device)
            # Ensure we store string in PushNotificationToken (as defined in model)
            if token.user_id != str(user_uuid):
                token.user_id = str(user_uuid)
                logger.info(f"Updated owner for device token: {device_token[:10]}...")
        else:
            # Create new token
            token = PushNotificationToken(
                user_id=str(user_uuid),
                device_token=device_token,
                platform=platform
            )
            db.session.add(token)
            logger.info(f"Registered new device token for user {user_id}")
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'token': token.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Token registration failed: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500
