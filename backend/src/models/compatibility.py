"""Compatibility model - stores calculated compatibility results between players."""
from datetime import datetime, timezone
from ..extensions import db


class Compatibility(db.Model):
    """Compatibility result between two players."""
    __tablename__ = "compatibility_results"
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Players (ordered: lower id first for consistency)
    player_a_id = db.Column(
        db.Integer,
        db.ForeignKey('profiles.id'),
        nullable=False,
        index=True
    )
    player_b_id = db.Column(
        db.Integer,
        db.ForeignKey('profiles.id'),
        nullable=False,
        index=True
    )
    
    # Compatibility scores
    overall_score = db.Column(db.Float, nullable=False)  # 0.0-1.0
    overall_percentage = db.Column(db.Integer, nullable=False)  # 0-100
    interpretation = db.Column(db.String(128), nullable=True)  # Text interpretation
    
    # Detailed breakdown
    # JSON format matches frontend: {
    #   "power_complement": 85,
    #   "domain_similarity": 92,
    #   "activity_overlap": 78,
    #   "truth_overlap": 95
    # }
    breakdown = db.Column(db.JSON, nullable=False)
    
    # Mutual interests and opportunities
    # JSON arrays of activity keys/topics
    mutual_activities = db.Column(db.JSON, nullable=True)
    growth_opportunities = db.Column(db.JSON, nullable=True)
    mutual_truth_topics = db.Column(db.JSON, nullable=True)
    
    # Blocked activities
    # JSON: {"reason": "hard_boundaries", "activities": ["bondage", "impact"]}
    blocked_activities = db.Column(db.JSON, nullable=True)
    
    # Boundary conflicts
    # JSON array: [{type, severity, description}]
    boundary_conflicts = db.Column(db.JSON, nullable=True)
    
    # Metadata
    calculation_version = db.Column(db.String(16), default="0.4", nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    player_a = db.relationship('Profile', foreign_keys=[player_a_id], backref='compatibility_as_a')
    player_b = db.relationship('Profile', foreign_keys=[player_b_id], backref='compatibility_as_b')
    
    # Ensure unique compatibility pair (unordered)
    __table_args__ = (
        db.Index('idx_compatibility_pair', 'player_a_id', 'player_b_id', unique=True),
    )
    
    def __repr__(self):
        return f"<Compatibility players={self.player_a_id},{self.player_b_id} score={self.overall_percentage}%>"
    
    @classmethod
    def get_or_create_key(cls, profile_id_1, profile_id_2):
        """Get ordered player IDs for consistent lookup."""
        # Always store with lower ID first
        if profile_id_1 < profile_id_2:
            return profile_id_1, profile_id_2
        return profile_id_2, profile_id_1
    
    def to_dict(self):
        """Convert compatibility to dictionary format."""
        return {
            'id': self.id,
            'player_a_id': self.player_a_id,
            'player_b_id': self.player_b_id,
            'overall_compatibility': {
                'score': self.overall_percentage,
                'interpretation': self.interpretation,
            },
            'breakdown': self.breakdown,
            'mutual_activities': self.mutual_activities or [],
            'growth_opportunities': self.growth_opportunities or [],
            'mutual_truth_topics': self.mutual_truth_topics or [],
            'blocked_activities': self.blocked_activities or {},
            'boundary_conflicts': self.boundary_conflicts or [],
            'calculation_version': self.calculation_version,
            'timestamp': self.created_at.isoformat(),
        }

