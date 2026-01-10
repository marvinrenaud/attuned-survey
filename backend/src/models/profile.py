"""Profile model - links to survey submissions and stores derived profile data."""
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .guid import GUID
from ..extensions import db


class Profile(db.Model):
    """Player profile derived from survey submission."""
    __tablename__ = "profiles"
    
    id = db.Column(db.Integer, primary_key=True)
    
    
    
    # Link to authenticated user (NEW - Migration 003)
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Link to survey submission
    submission_id = db.Column(
        db.String(128), 
        db.ForeignKey('survey_submissions.submission_id'),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Anonymous support (NEW - Migration 003)
    is_anonymous = db.Column(db.Boolean, nullable=False, default=False, index=True)
    anonymous_session_id = db.Column(db.String(255), nullable=True, index=True)
    last_accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profile metadata
    profile_version = db.Column(db.String(16), default="0.4", nullable=False)
    survey_version = db.Column(db.String(16), default="0.4", nullable=False)  # NEW - Migration 003
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Derived profile data (stored as JSON for flexibility)
    # This matches the structure from frontend/src/lib/scoring/profileCalculator.js
    power_dynamic = db.Column(db.JSON, nullable=False)  # {orientation, intensity, preference}
    arousal_propensity = db.Column(db.JSON, nullable=False)  # {physical, emotional, psychological}
    domain_scores = db.Column(db.JSON, nullable=False)  # {domain_name: score}
    activities = db.Column(db.JSON, nullable=False)  # {activity_key: preference_score}
    truth_topics = db.Column(db.JSON, nullable=False)  # {topic: openness_score}
    boundaries = db.Column(db.JSON, nullable=False)  # {hard_limits: [], soft_limits: [], maybe_items: []}
    anatomy = db.Column(db.JSON, nullable=False, default=dict)  # {anatomy_self: [], anatomy_preference: []}
    activity_tags = db.Column(db.JSON, nullable=True)  # Optional activity tags
    
    # Relationships
    submission = db.relationship(
        'SurveySubmission',
        backref=db.backref('profile', uselist=False, lazy=True)
    )
    
    def __repr__(self):
        return f"<Profile {self.id} submission={self.submission_id}>"
    
    def to_dict(self):
        """Convert profile to dictionary format."""
        return {
            'id': self.id,
            'user_id': str(self.user_id) if self.user_id else None,
            'submission_id': self.submission_id,
            'is_anonymous': self.is_anonymous,
            'anonymous_session_id': self.anonymous_session_id,
            'profile_version': self.profile_version,
            'survey_version': self.survey_version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'power_dynamic': self.power_dynamic or {},
            'arousal_propensity': self.arousal_propensity or {},
            'domain_scores': self.domain_scores or {},
            'activities': self.activities or {},
            'truth_topics': self.truth_topics or {},
            'boundaries': self.boundaries or {},
            'anatomy': self.anatomy or {},
            'activity_tags': self.activity_tags or [],
        }

