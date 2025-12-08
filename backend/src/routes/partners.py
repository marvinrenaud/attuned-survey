"""Partner connection and management routes."""
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid

from ..extensions import db
from ..models.user import User

# Import PartnerConnection and RememberedPartner models
# These will need to be created based on the migrations
try:
    from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, or_
    from sqlalchemy.orm import relationship
    
    class PartnerConnection(db.Model):
        __tablename__ = 'partner_connections'
        
        id = Column(Integer, primary_key=True)
        requester_user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
        requester_display_name = Column(Text)  # Added via migration
        recipient_email = Column(Text, nullable=False)
        recipient_user_id = Column(String(36), ForeignKey('users.id'))
        recipient_display_name = Column(Text)  # Added via migration
        status = Column(SQLEnum('pending', 'accepted', 'declined', 'expired', name='connection_status_enum'), nullable=False, default='pending')
        connection_token = Column(Text, unique=True, nullable=False)
        expires_at = Column(DateTime, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def to_dict(self):
            return {
                'id': self.id,
                'requester_user_id': str(self.requester_user_id),
                'requester_display_name': self.requester_display_name,
                'recipient_email': self.recipient_email,
                'recipient_user_id': str(self.recipient_user_id) if self.recipient_user_id else None,
                'recipient_display_name': self.recipient_display_name,
                'status': self.status,
                'connection_token': self.connection_token,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
    
    class RememberedPartner(db.Model):
        __tablename__ = 'remembered_partners'
        
        id = Column(Integer, primary_key=True)
        user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
        partner_user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
        partner_name = Column(Text, nullable=False)
        partner_email = Column(Text, nullable=False)
        last_played_at = Column(DateTime, default=datetime.utcnow)
        created_at = Column(DateTime, default=datetime.utcnow)
        
        def to_dict(self):
            return {
                'id': self.id,
                'user_id': str(self.user_id),
                'partner_user_id': str(self.partner_user_id),
                'partner_name': self.partner_name,
                'partner_email': self.partner_email,
                'last_played_at': self.last_played_at.isoformat() if self.last_played_at else None,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
    
except Exception as e:
    current_app.logger.error(f"Failed to define partner models: {str(e)}")

partners_bp = Blueprint('partners', __name__, url_prefix='/api/partners')


@partners_bp.route('/connect', methods=['POST'])
def create_connection_request():
    """
    Create a partner connection request (FR-55).
    
    Expected payload:
    {
        "requester_user_id": "uuid",
        "recipient_email": "partner@example.com"
    }
    """
    try:
        data = request.get_json()
        
        requester_id = data.get('requester_user_id')
        recipient_email = data.get('recipient_email')
        
        if not requester_id or not recipient_email:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if requester exists
        requester = User.query.filter_by(id=requester_id).first()
        if not requester:
            return jsonify({'error': 'Requester not found'}), 404
        
        # Generate connection token
        connection_token = str(uuid.uuid4())
        
        # Check if recipient exists
        recipient = User.query.filter_by(email=recipient_email).first()
        recipient_id = recipient.id if recipient else None
        
        # Create connection request
        connection = PartnerConnection(
            requester_user_id=requester_id,
            recipient_email=recipient_email,
            recipient_user_id=recipient_id,
            status='pending',
            connection_token=connection_token,
            expires_at=datetime.utcnow() + timedelta(minutes=5)  # FR-56: 5 minute expiry
        )
        
        db.session.add(connection)
        db.session.commit()
        
        # TODO: Send push notification to recipient
        # This would integrate with FCM/APNs
        
        current_app.logger.info(f"Connection request created: {connection.id}")
        
        return jsonify({
            'success': True,
            'connection': connection.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Connection request failed: {str(e)}")
        return jsonify({'error': 'Failed to create connection'}), 500


@partners_bp.route('/connections/<connection_id>/accept', methods=['POST'])
def accept_connection(connection_id):
    """
    Accept a partner connection request (FR-57).
    
    Expected payload:
    {
        "recipient_user_id": "uuid"
    }
    """
    try:
        data = request.get_json()
        recipient_id = data.get('recipient_user_id')
        
        if not recipient_id:
            return jsonify({'error': 'Missing recipient_user_id'}), 400
        
        connection = PartnerConnection.query.filter_by(id=connection_id).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Check if expired
        if connection.expires_at < datetime.utcnow():
            connection.status = 'expired'
            db.session.commit()
            return jsonify({'error': 'Connection request expired'}), 410
        
        # Accept connection
        connection.status = 'accepted'
        connection.recipient_user_id = recipient_id
        
        # Add to remembered partners for both users
        requester_partner = RememberedPartner(
            user_id=connection.requester_user_id,
            partner_user_id=recipient_id,
            partner_name=User.query.get(recipient_id).display_name or 'Partner',
            partner_email=connection.recipient_email,
            last_played_at=datetime.utcnow()
        )
        
        recipient_partner = RememberedPartner(
            user_id=recipient_id,
            partner_user_id=connection.requester_user_id,
            partner_name=User.query.get(connection.requester_user_id).display_name or 'Partner',
            partner_email=User.query.get(connection.requester_user_id).email,
            last_played_at=datetime.utcnow()
        )
        
        db.session.add(requester_partner)
        db.session.add(recipient_partner)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'connection': connection.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Accept connection failed: {str(e)}")
        return jsonify({'error': 'Failed to accept connection'}), 500


@partners_bp.route('/connections/<connection_id>/decline', methods=['POST'])
def decline_connection(connection_id):
    """
    Decline a partner connection request (FR-57).
    """
    try:
        connection = PartnerConnection.query.filter_by(id=connection_id).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        connection.status = 'declined'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'connection': connection.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Decline connection failed: {str(e)}")
        return jsonify({'error': 'Failed to decline connection'}), 500


@partners_bp.route('/connections/<user_id>', methods=['GET'])
def get_connections(user_id):
    """
    Get all partner connections for a user (pending, accepted, declined, expired).
    """
    try:
        # Get user to find their email
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Find connections where:
        # 1. User is the requester
        # 2. User is the recipient (by email)
        # 3. User is the recipient (by ID - for accepted ones)
        connections = PartnerConnection.query.filter(
            or_(
                PartnerConnection.requester_user_id == user_id,
                PartnerConnection.recipient_email == user.email,
                PartnerConnection.recipient_user_id == user_id
            )
        ).order_by(PartnerConnection.created_at.desc()).all()
        
        return jsonify({
            'connections': [c.to_dict() for c in connections]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get connections failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve connections'}), 500



@partners_bp.route('/remembered/<user_id>', methods=['GET'])
def get_remembered_partners(user_id):
    """
    Get list of remembered partners for a user (FR-60).
    Returns up to 10 most recent partners.
    """
    try:
        partners = RememberedPartner.query\
            .filter_by(user_id=user_id)\
            .order_by(RememberedPartner.last_played_at.desc())\
            .limit(10)\
            .all()
        
        return jsonify({
            'partners': [p.to_dict() for p in partners]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get remembered partners failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve partners'}), 500


@partners_bp.route('/remembered/<partner_id>', methods=['DELETE'])
def remove_remembered_partner(partner_id):
    """
    Remove a partner from remembered list (FR-61).
    """
    try:
        partner = RememberedPartner.query.filter_by(id=partner_id).first()
        
        if not partner:
            return jsonify({'error': 'Partner not found'}), 404
        
        db.session.delete(partner)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Partner removed'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Remove partner failed: {str(e)}")
        return jsonify({'error': 'Failed to remove partner'}), 500


from datetime import timedelta  # Add this import at the top

