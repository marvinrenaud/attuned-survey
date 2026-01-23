"""Influencer model - marketing partners with promo codes."""
from datetime import datetime
from ..extensions import db


class Influencer(db.Model):
    """Marketing influencer who can have promo codes assigned."""
    __tablename__ = "influencers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    platform = db.Column(db.String(50))  # 'tiktok', 'instagram', 'podcast', 'youtube'
    status = db.Column(db.String(20), default='active')  # 'active', 'paused', 'inactive'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    promo_codes = db.relationship('PromoCode', backref='influencer', lazy='dynamic')

    def __repr__(self):
        return f'<Influencer {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'platform': self.platform,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
