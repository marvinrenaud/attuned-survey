"""Session model - stores game session configuration and state."""
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB
from .guid import GUID
from ..extensions import db
import uuid


class Session(db.Model):
    """Game session between two players."""
    __tablename__ = "sessions"
    
    # Primary key
    session_id = db.Column(db.String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Legacy players (kept for backward compatibility)
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
    
    # NEW MVP Fields (Migration 005) - Support authenticated + anonymous users
    primary_user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    primary_profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=True, index=True)
    partner_user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    partner_profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Anonymous partner information
    partner_anonymous_name = db.Column(db.String(255), nullable=True)
    partner_anonymous_anatomy = db.Column(JSONB, nullable=True)
    
    # Game configuration
    intimacy_level = db.Column(
        db.Enum('G', 'R', 'X', name='intimacy_level_enum', create_type=False),
        nullable=False, default='R'
    )
    skip_count = db.Column(db.Integer, nullable=False, default=0)
    
    # Session ownership and confirmation
    session_owner_user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    connection_confirmed_at = db.Column(db.DateTime, nullable=True)
    
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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Rules and configuration (JSON for flexibility)
    rules = db.Column(db.JSON, nullable=True)  # {avoid_maybe_until: 6, etc.}

    # NEW Gameplay Fields (Migration 006)
    players = db.Column(JSONB, nullable=True)  # List of player objects
    game_settings = db.Column(JSONB, nullable=True)  # {intimacy_level, mode, etc.}
    current_turn_state = db.Column(JSONB, nullable=True)  # {status, primary_idx, etc.}
    
    # Relationships
    player_a_profile = db.relationship('Profile', foreign_keys=[player_a_profile_id], backref='sessions_as_a')
    player_b_profile = db.relationship('Profile', foreign_keys=[player_b_profile_id], backref='sessions_as_b')
    
    def __repr__(self):
        return f"<Session {self.session_id} players={self.player_a_profile_id},{self.player_b_profile_id}>"
    
    def to_dict(self):
        """Convert session to dictionary format."""
        return {
            'session_id': self.session_id,
            # Legacy fields
            'player_a_profile_id': self.player_a_profile_id,
            'player_b_profile_id': self.player_b_profile_id,
            # New MVP fields
            'primary_user_id': str(self.primary_user_id) if self.primary_user_id else None,
            'primary_profile_id': self.primary_profile_id,
            'partner_user_id': str(self.partner_user_id) if self.partner_user_id else None,
            'partner_profile_id': self.partner_profile_id,
            'partner_anonymous_name': self.partner_anonymous_name,
            'partner_anonymous_anatomy': self.partner_anonymous_anatomy or {},
            'intimacy_level': self.intimacy_level,
            'skip_count': self.skip_count,
            'session_owner_user_id': str(self.session_owner_user_id) if self.session_owner_user_id else None,
            'connection_confirmed_at': self.connection_confirmed_at.isoformat() if self.connection_confirmed_at else None,
            # Existing fields
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
            'rules': self.rules or {},
            # New Gameplay Fields
            'players': self.players or [],
            'game_settings': self.game_settings or {},
            'current_turn_state': self.current_turn_state or {},
        }

