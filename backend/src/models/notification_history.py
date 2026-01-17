"""SQLAlchemy model for the notifications table."""
from datetime import datetime
from ..extensions import db
from .guid import GUID


class Notification(db.Model):
    """Push notification history and queue."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipient_user_id = db.Column(
        GUID(), 
        db.ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False
    )
    sender_user_id = db.Column(
        GUID(), 
        db.ForeignKey('users.id', ondelete='SET NULL'), 
        nullable=True
    )
    notification_type = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    body = db.Column(db.String, nullable=False)
    data = db.Column(db.JSON, default=dict)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'recipient_user_id': str(self.recipient_user_id),
            'sender_user_id': str(self.sender_user_id) if self.sender_user_id else None,
            'notification_type': self.notification_type,
            'title': self.title,
            'body': self.body,
            'data': self.data,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
