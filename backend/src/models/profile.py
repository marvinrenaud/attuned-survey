"""Profile model - links to survey submissions and stores derived profile data."""
from datetime import datetime
from ..extensions import db


class Profile(db.Model):
    """Player profile derived from survey submission."""
    __tablename__ = "profiles"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Link to survey submission
    submission_id = db.Column(
        db.String(128), 
        db.ForeignKey('survey_submissions.submission_id'),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Profile metadata
    profile_version = db.Column(db.String(16), default="0.4", nullable=False)
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
            'submission_id': self.submission_id,
            'profile_version': self.profile_version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'power_dynamic': self.power_dynamic,
            'arousal_propensity': self.arousal_propensity,
            'domain_scores': self.domain_scores,
            'activities': self.activities,
            'truth_topics': self.truth_topics,
            'boundaries': self.boundaries,
            'activity_tags': self.activity_tags,
        }

