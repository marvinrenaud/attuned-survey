from ..extensions import db
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from .guid import GUID

class PartnerConnection(db.Model):
    __tablename__ = 'partner_connections'
    
    id = Column(Integer, primary_key=True)
    requester_user_id = Column(GUID(), ForeignKey('users.id'), nullable=False)
    requester_display_name = Column(Text)  # Added via migration
    recipient_email = Column(Text, nullable=False)
    recipient_user_id = Column(GUID(), ForeignKey('users.id'))
    recipient_display_name = Column(Text)  # Added via migration
    status = Column(SQLEnum('pending', 'accepted', 'declined', 'expired', 'disconnected', name='connection_status_enum'), nullable=False, default='pending')
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
    user_id = Column(GUID(), ForeignKey('users.id'), nullable=False)
    partner_user_id = Column(GUID(), nullable=False)
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
