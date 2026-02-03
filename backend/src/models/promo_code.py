"""PromoCode model - discount codes for subscription purchases."""
from datetime import datetime, timezone
from ..extensions import db


class PromoCode(db.Model):
    """Promotional discount code linked to an influencer."""
    __tablename__ = "promo_codes"

    id = db.Column(db.Integer, primary_key=True)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencers.id', ondelete='SET NULL'))
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percent = db.Column(db.Integer, default=20)
    stripe_coupon_id = db.Column(db.String(255))
    revenuecat_offering_id = db.Column(db.String(255), default='discounted_20_percent')
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    max_redemptions = db.Column(db.Integer)
    redemption_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    redemptions = db.relationship('PromoRedemption', backref='promo_code', lazy='dynamic')

    def __repr__(self):
        return f'<PromoCode {self.code}>'

    def is_valid(self):
        """
        Check if code can be redeemed.
        Returns tuple: (is_valid: bool, error_message: str or None)

        Note: This only checks the code's own validity (active, not expired, under max).
        User-specific checks (already used by this user) are done in the service layer.
        """
        if not self.is_active:
            return False, 'Code is inactive'

        if self.expires_at:
            # Handle both naive and aware datetimes
            expires = self.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires:
                return False, 'Code has expired'

        if self.max_redemptions and self.redemption_count >= self.max_redemptions:
            return False, 'Maximum redemptions reached'

        return True, None

    def to_dict(self):
        """Return public-safe fields for validation response."""
        return {
            'code': self.code,
            'discount_percent': self.discount_percent,
            'offering_id': self.revenuecat_offering_id,
            'influencer_name': self.influencer.name if self.influencer else None
        }
