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


@notifications_bp.route('/mark-all-read', methods=['POST'])
@token_required
def mark_all_read(current_user_id):
    """
    Mark all notifications as read for the authenticated user.
    
    Response:
    {
        "success": true,
        "marked_count": 5
    }
    """
    from ..models.notification_history import Notification
    from datetime import datetime
    
    try:
        user_uuid = uuid.UUID(str(current_user_id))
        
        # Update all unread notifications for this user
        result = Notification.query.filter_by(
            recipient_user_id=user_uuid,
            is_read=False
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        
        db.session.commit()
        logger.info(f"Marked {result} notifications as read for user {current_user_id}")
        
        return jsonify({
            'success': True,
            'marked_count': result
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Mark all read failed: {str(e)}")
        return jsonify({'error': 'Failed to mark notifications as read'}), 500


@notifications_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@token_required
def mark_read(current_user_id, notification_id):
    """
    Mark a specific notification as read.
    Only works if the notification belongs to the authenticated user.
    
    Response:
    {
        "success": true
    }
    """
    from ..models.notification_history import Notification
    from datetime import datetime
    
    try:
        user_uuid = uuid.UUID(str(current_user_id))
        
        # Find the notification (must belong to current user)
        notification = Notification.query.filter_by(
            id=notification_id,
            recipient_user_id=user_uuid
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
            logger.info(f"Marked notification {notification_id} as read")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Mark read failed: {str(e)}")
        return jsonify({'error': 'Failed to mark notification as read'}), 500
