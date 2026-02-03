"""SessionActivity model - stores generated activities for game sessions."""
from datetime import datetime, timezone
from ..extensions import db


class SessionActivity(db.Model):
    """Activity generated for a specific session."""
    __tablename__ = "session_activities"
    
    # Composite primary key
    session_id = db.Column(
        db.String(128),
        db.ForeignKey('sessions.session_id'),
        primary_key=True
    )
    seq = db.Column(db.Integer, primary_key=True)  # Step number (1-25)
    
    # Link to activity bank (nullable if AI-generated or custom)
    activity_id = db.Column(
        db.Integer,
        db.ForeignKey('activities.activity_id'),
        nullable=True
    )
    
    # Denormalized activity data (for historical accuracy even if source changes)
    type = db.Column(db.String(16), nullable=False)  # truth, dare
    rating = db.Column(db.String(1), nullable=False)  # G, R, X
    intensity = db.Column(db.Integer, nullable=False)  # 1-5
    script = db.Column(db.JSON, nullable=False)  # Complete script
    tags = db.Column(db.JSON, nullable=True)  # Activity tags
    
    # Actor roles for this specific session
    # Stored as JSON: {"active_player": "A"|"B", "partner_player": "A"|"B"}
    roles = db.Column(db.JSON, nullable=True)
    
    # Provenance tracking
    source = db.Column(db.String(32), nullable=False)  # bank, ai_generated, user_submitted
    template_id = db.Column(db.Integer, nullable=True)  # Original activity_id if from bank
    
    # Validation checks (from validator)
    # Stored as JSON: {
    #   "respects_hard_limits": true,
    #   "uses_yes_overlap": true,
    #   "maybe_items_present": false,
    #   "anatomy_ok": true,
    #   "power_alignment": true,
    #   "notes": "..."
    # }
    checks = db.Column(db.JSON, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    session = db.relationship('Session', backref=db.backref('activities', lazy=True, order_by='SessionActivity.seq'))
    activity = db.relationship('Activity', backref='session_uses')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_session_seq', 'session_id', 'seq'),
    )
    
    def __repr__(self):
        return f"<SessionActivity session={self.session_id} seq={self.seq} type={self.type}>"
    
    def to_dict(self):
        """Convert session activity to dictionary format."""
        return {
            'session_id': self.session_id,
            'seq': self.seq,
            'activity_id': self.activity_id,
            'type': self.type,
            'rating': self.rating,
            'intensity': self.intensity,
            'script': self.script,
            'tags': self.tags or [],
            'roles': self.roles,
            'source': self.source,
            'template_id': self.template_id,
            'checks': self.checks or {},
            'created_at': self.created_at.isoformat(),
        }

