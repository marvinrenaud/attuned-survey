"""Activity model - stores activity bank templates."""
from datetime import datetime
from sqlalchemy.dialects.postgresql import ENUM
from ..extensions import db

# Allowed boundary keys (8-key taxonomy)
ALLOWED_BOUNDARIES = [
    'hardBoundaryImpact', 'hardBoundaryRestrain', 'hardBoundaryBreath',
    'hardBoundaryDegrade', 'hardBoundaryPublic', 'hardBoundaryRecord',
    'hardBoundaryAnal', 'hardBoundaryWatersports'
]

# Allowed body parts
ALLOWED_BODYPARTS = ['penis', 'vagina', 'breasts']


class Activity(db.Model):
    """Activity template in the bank."""
    __tablename__ = "activities"
    
    # Primary key
    activity_id = db.Column(db.Integer, primary_key=True)
    
    # Activity classification
    type = db.Column(db.String(16), nullable=False, index=True)  # truth, dare
    rating = db.Column(db.String(1), nullable=False, index=True)  # G, R, X
    intensity = db.Column(db.Integer, nullable=False, index=True)  # 1-5
    
    # Activity content
    # Script format: {"steps": [{"actor": "A"|"B", "do": "action description"}]}
    script = db.Column(db.JSON, nullable=False)
    
    # Metadata
    tags = db.Column(db.JSON, nullable=True)  # ["couple", "group", "verbal", etc.]
    source = db.Column(db.String(32), nullable=False, default='bank')  # bank, ai_generated, user_submitted
    approved = db.Column(db.Boolean, nullable=False, default=True)
    
    # Optional: hard limit keys that this activity requires
    # e.g., ["impact_play", "bondage"] - used to filter against player boundaries
    hard_limit_keys = db.Column(db.JSON, nullable=True)
    
    # AI-enriched metadata (added for personalization)
    power_role = db.Column(db.String(16), nullable=True, index=True)  # top, bottom, switch, neutral
    preference_keys = db.Column(db.JSON, nullable=True)  # [massage, oral, bondage, etc.]
    domains = db.Column(db.JSON, nullable=True)  # [sensual, playful, power, connection, exploration]
    intensity_modifiers = db.Column(db.JSON, nullable=True)  # [gentle, intense, edgy, taboo, etc.]
    requires_consent_negotiation = db.Column(db.Boolean, default=False, nullable=True)
    
    # New: Audience scope, boundaries, anatomy requirements, and versioning
    audience_scope = db.Column(
        ENUM('couples', 'groups', 'all', name='audience_scope_enum', create_type=False),
        nullable=False,
        default='all',
        index=True
    )
    hard_boundaries = db.Column(db.JSON, nullable=False, default=list)  # 8-key boundary taxonomy
    required_bodyparts = db.Column(db.JSON, nullable=False, default=lambda: {"active": [], "partner": []})
    activity_uid = db.Column(db.String(64), unique=True, index=True)  # SHA256 hash for deduplication
    source_version = db.Column(db.String(32))  # Source spreadsheet version
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    archived_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes for common queries
    __table_args__ = (
        db.Index('idx_activity_lookup', 'type', 'rating', 'intensity', 'approved'),
    )
    
    def __repr__(self):
        return f"<Activity {self.activity_id} {self.type} {self.rating}{self.intensity}>"
    
    def validate_boundaries(self) -> bool:
        """Validate hard_boundaries contains only allowed keys."""
        if not isinstance(self.hard_boundaries, list):
            return False
        return all(b in ALLOWED_BOUNDARIES for b in self.hard_boundaries)
    
    def validate_bodyparts(self) -> bool:
        """Validate required_bodyparts structure and values."""
        if not isinstance(self.required_bodyparts, dict):
            return False
        if 'active' not in self.required_bodyparts or 'partner' not in self.required_bodyparts:
            return False
        active = self.required_bodyparts['active']
        partner = self.required_bodyparts['partner']
        if not isinstance(active, list) or not isinstance(partner, list):
            return False
        return (all(bp in ALLOWED_BODYPARTS for bp in active) and
                all(bp in ALLOWED_BODYPARTS for bp in partner))
    
    def to_dict(self):
        """Convert activity to dictionary format."""
        return {
            'activity_id': self.activity_id,
            'type': self.type,
            'rating': self.rating,
            'intensity': self.intensity,
            'script': self.script,
            'tags': self.tags or [],
            'source': self.source,
            'approved': self.approved,
            'hard_limit_keys': self.hard_limit_keys or [],
            'power_role': self.power_role,
            'preference_keys': self.preference_keys or [],
            'domains': self.domains or [],
            'intensity_modifiers': self.intensity_modifiers or [],
            'requires_consent_negotiation': self.requires_consent_negotiation,
            'audience_scope': self.audience_scope,
            'hard_boundaries': self.hard_boundaries or [],
            'required_bodyparts': self.required_bodyparts or {"active": [], "partner": []},
            'activity_uid': self.activity_uid,
            'source_version': self.source_version,
            'is_active': self.is_active,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    def matches_criteria(self, type_filter=None, rating_filter=None, 
                        intensity_min=None, intensity_max=None, 
                        exclude_hard_limits=None):
        """Check if activity matches search criteria."""
        if type_filter and self.type != type_filter:
            return False
        
        if rating_filter and self.rating != rating_filter:
            return False
        
        if intensity_min is not None and self.intensity < intensity_min:
            return False
        
        if intensity_max is not None and self.intensity > intensity_max:
            return False
        
        if exclude_hard_limits and self.hard_limit_keys:
            # Check if any of this activity's hard limits are in the exclusion list
            if any(limit in exclude_hard_limits for limit in self.hard_limit_keys):
                return False
        
        return True

