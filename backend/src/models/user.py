"""User model - authenticated user accounts linked to Supabase Auth."""
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..extensions import db


class User(db.Model):
    """Authenticated user account (linked to Supabase auth.users)."""
    __tablename__ = "users"
    
    # Primary key from Supabase Auth
    id = db.Column(UUID(as_uuid=True), primary_key=True)
    
    # Authentication
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    auth_provider = db.Column(db.String(20), nullable=False, default='email')  # email, google, apple, facebook
    
    # Profile information
    display_name = db.Column(db.String(255))
    demographics = db.Column(JSONB, nullable=False, default=dict)  # {gender, orientation, relationship_structure}
    
    # Subscription
    subscription_tier = db.Column(db.String(20), nullable=False, default='free')  # free, premium
    subscription_expires_at = db.Column(db.DateTime)
    daily_activity_count = db.Column(db.Integer, nullable=False, default=0)
    daily_activity_reset_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Preferences
    profile_sharing_setting = db.Column(db.String(30), nullable=False, default='overlapping_only')
    notification_preferences = db.Column(JSONB, nullable=False, default=dict)
    
    # Status
    onboarding_completed = db.Column(db.Boolean, nullable=False, default=False)
    last_login_at = db.Column(db.DateTime)
    oauth_metadata = db.Column(JSONB)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'auth_provider': self.auth_provider,
            'display_name': self.display_name,
            'demographics': self.demographics,
            'subscription_tier': self.subscription_tier,
            'subscription_expires_at': self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
            'daily_activity_count': self.daily_activity_count,
            'daily_activity_reset_at': self.daily_activity_reset_at.isoformat() if self.daily_activity_reset_at else None,
            'profile_sharing_setting': self.profile_sharing_setting,
            'notification_preferences': self.notification_preferences,
            'onboarding_completed': self.onboarding_completed,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
