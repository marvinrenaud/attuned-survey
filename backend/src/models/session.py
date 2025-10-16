"""Session model - stores game session configuration and state."""
from datetime import datetime
from ..extensions import db
import uuid


class Session(db.Model):
    """Game session between two players."""
    __tablename__ = "sessions"
    
    # Primary key
    session_id = db.Column(db.String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Players
    player_a_profile_id = db.Column(
        db.Integer,
        db.ForeignKey('profiles.id'),
        nullable=False,
        index=True
    )
    player_b_profile_id = db.Column(
        db.Integer,
        db.ForeignKey('profiles.id'),
        nullable=False,
        index=True
    )
    
    # Session configuration
    rating = db.Column(db.String(1), nullable=False, default='R')  # G, R, X
    activity_type = db.Column(db.String(16), nullable=False, default='random')  # random, truth, dare
    target_activities = db.Column(db.Integer, nullable=False, default=25)
    bank_ratio = db.Column(db.Float, nullable=False, default=0.5)  # 0.0-1.0, ratio of bank vs AI activities
    
    # Session state tracking
    truth_so_far = db.Column(db.Integer, nullable=False, default=0)
    dare_so_far = db.Column(db.Integer, nullable=False, default=0)
    current_step = db.Column(db.Integer, nullable=False, default=0)
    
    # Session status
    status = db.Column(db.String(32), nullable=False, default='active')  # active, completed, abandoned
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Rules and configuration (JSON for flexibility)
    rules = db.Column(db.JSON, nullable=True)  # {avoid_maybe_until: 6, etc.}
    
    # Relationships
    player_a_profile = db.relationship('Profile', foreign_keys=[player_a_profile_id], backref='sessions_as_a')
    player_b_profile = db.relationship('Profile', foreign_keys=[player_b_profile_id], backref='sessions_as_b')
    
    def __repr__(self):
        return f"<Session {self.session_id} players={self.player_a_profile_id},{self.player_b_profile_id}>"
    
    def to_dict(self):
        """Convert session to dictionary format."""
        return {
            'session_id': self.session_id,
            'player_a_profile_id': self.player_a_profile_id,
            'player_b_profile_id': self.player_b_profile_id,
            'rating': self.rating,
            'activity_type': self.activity_type,
            'target_activities': self.target_activities,
            'bank_ratio': self.bank_ratio,
            'truth_so_far': self.truth_so_far,
            'dare_so_far': self.dare_so_far,
            'current_step': self.current_step,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'rules': self.rules,
        }

