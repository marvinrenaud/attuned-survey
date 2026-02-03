"""PromoRedemption model - tracks when users redeem promo codes."""
from datetime import datetime, timezone
from ..extensions import db
from .guid import GUID


class PromoRedemption(db.Model):
    """Record of a user redeeming a promo code for a subscription."""
    __tablename__ = "promo_redemptions"

    id = db.Column(db.Integer, primary_key=True)
    promo_code_id = db.Column(db.Integer, db.ForeignKey('promo_codes.id'))
    user_id = db.Column(GUID(), db.ForeignKey('users.id'))
    subscription_product = db.Column(db.String(255))  # e.g., 'attuned_monthly'
    original_price = db.Column(db.Numeric(10, 2))  # May be NULL if unknown
    discounted_price = db.Column(db.Numeric(10, 2))  # Actual amount paid
    redeemed_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = db.relationship('User', backref='promo_redemptions')

    def __repr__(self):
        return f'<PromoRedemption {self.id} user={self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'promo_code_id': self.promo_code_id,
            'subscription_product': self.subscription_product,
            'original_price': float(self.original_price) if self.original_price else None,
            'discounted_price': float(self.discounted_price) if self.discounted_price else None,
            'redeemed_at': self.redeemed_at.isoformat() if self.redeemed_at else None
        }
