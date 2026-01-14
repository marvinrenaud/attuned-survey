"""User model - authenticated user accounts linked to Supabase Auth."""
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..extensions import db
from .guid import GUID


class User(db.Model):
    """Authenticated user account (linked to Supabase auth.users)."""
    __tablename__ = "users"
    
    # Primary key from Supabase Auth
    id = db.Column(GUID(), primary_key=True)
    
    # Authentication
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    auth_provider = db.Column(
        db.Enum('email', 'google', 'apple', 'facebook', name='auth_provider_enum', create_type=False),
        nullable=False, default='email'
    )
    
    # Profile information
    display_name = db.Column(db.String(255))
    demographics = db.Column(JSONB, nullable=False, default=dict)  # {gender, orientation, relationship_structure}
    
    # Anatomy - What user has (NEW - Migration 010)
    has_penis = db.Column(db.Boolean, nullable=False, default=False)
    has_vagina = db.Column(db.Boolean, nullable=False, default=False)
    has_breasts = db.Column(db.Boolean, nullable=False, default=False)
    
    # Anatomy - What user likes in partners (NEW - Migration 010)
    likes_penis = db.Column(db.Boolean, nullable=False, default=False)
    likes_vagina = db.Column(db.Boolean, nullable=False, default=False)
    likes_breasts = db.Column(db.Boolean, nullable=False, default=False)
    
    # Subscription
    subscription_tier = db.Column(
        db.Enum('free', 'premium', name='subscription_tier_enum', create_type=False),
        nullable=False, default='free'
    )
    subscription_expires_at = db.Column(db.DateTime)
    daily_activity_count = db.Column(db.Integer, nullable=False, default=0)
    daily_activity_reset_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Preferences
    profile_sharing_setting = db.Column(
        db.Enum('all_responses', 'overlapping_only', 'demographics_only', name='profile_sharing_enum', create_type=False),
        nullable=False, default='overlapping_only'
    )
    notification_preferences = db.Column(JSONB, nullable=False, default=dict)
    
    # Status
    profile_completed = db.Column(db.Boolean, nullable=False, default=False, index=True)  # NEW: Can user play?
    onboarding_completed = db.Column(db.Boolean, nullable=False, default=False)  # Survey completed?
    last_login_at = db.Column(db.DateTime)
    oauth_metadata = db.Column(JSONB)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.email}>'
    
    def get_anatomy_self_array(self):
        """Convert has_* booleans to array for backward compatibility."""
        anatomy = []
        if self.has_penis:
            anatomy.append('penis')
        if self.has_vagina:
            anatomy.append('vagina')
        if self.has_breasts:
            anatomy.append('breasts')
        return anatomy
    
    def get_anatomy_preference_array(self):
        """Convert likes_* booleans to array for backward compatibility."""
        anatomy = []
        if self.likes_penis:
            anatomy.append('penis')
        if self.likes_vagina:
            anatomy.append('vagina')
        if self.likes_breasts:
            anatomy.append('breasts')
        return anatomy

    def to_dict(self):
        return {
            'id': str(self.id),
            'submission_id': self.submission.submission_id if getattr(self, 'submission', None) else None,
            'email': self.email,
            'auth_provider': self.auth_provider,
            'display_name': self.display_name,
            'demographics': self.demographics or {},
            'has_penis': self.has_penis,
            'has_vagina': self.has_vagina,
            'has_breasts': self.has_breasts,
            'likes_penis': self.likes_penis,
            'likes_vagina': self.likes_vagina,
            'likes_breasts': self.likes_breasts,
            'anatomy_self': self.get_anatomy_self_array(),  # Computed for backward compat
            'anatomy_preference': self.get_anatomy_preference_array(),  # Computed for backward compat
            'subscription_tier': self.subscription_tier,
            'subscription_expires_at': self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
            'daily_activity_count': self.daily_activity_count,
            'daily_activity_reset_at': self.daily_activity_reset_at.isoformat() if self.daily_activity_reset_at else None,
            'profile_sharing_setting': self.profile_sharing_setting,
            'notification_preferences': self.notification_preferences or {},
            'profile_completed': self.profile_completed,
            'onboarding_completed': self.onboarding_completed,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
