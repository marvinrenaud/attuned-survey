from flask import Blueprint, jsonify, request, current_app
from ..extensions import db
from ..models.notification import PushNotificationToken
from ..models.user import User

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/register', methods=['POST'])
def register_token():
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
            
        # Verify user exists
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Check if token already exists
        token = PushNotificationToken.query.filter_by(device_token=device_token).first()
        
        if token:
            # Update user_id if changed (e.g. user logged in on same device)
            if token.user_id != user_id:
                token.user_id = user_id
                current_app.logger.info(f"Updated owner for device token: {device_token[:10]}...")
        else:
            # Create new token
            token = PushNotificationToken(
                user_id=user_id,
                device_token=device_token,
                platform=platform
            )
            db.session.add(token)
            current_app.logger.info(f"Registered new device token for user {user_id}")
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'token': token.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Token registration failed: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500
