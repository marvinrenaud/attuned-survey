from ..extensions import db
from datetime import datetime, timezone
from .guid import GUID

class PushNotificationToken(db.Model):
    __tablename__ = 'push_notification_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    device_token = db.Column(db.String, unique=True, nullable=False)
    platform = db.Column(
        db.Enum('ios', 'android', name='platform_enum', create_type=False),
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_token': self.device_token,
            'platform': self.platform,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
