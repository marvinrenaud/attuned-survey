from datetime import datetime
from ..extensions import db

class UserActivityHistory(db.Model):
    __tablename__ = 'user_activity_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    anonymous_session_id = db.Column(db.String, nullable=True)
    session_id = db.Column(db.String, db.ForeignKey('sessions.session_id', ondelete='CASCADE'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.activity_id', ondelete='SET NULL'), nullable=True)
    activity_type = db.Column(db.String, nullable=False)  # 'truth' or 'dare'
    was_skipped = db.Column(db.Boolean, default=False, nullable=False)
    feedback_type = db.Column(db.String, nullable=True)  # 'like', 'dislike', 'neutral'
    feedback_executed = db.Column(db.Boolean, nullable=True)
    presented_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    theme_tags = db.Column(db.JSON, default=list)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'anonymous_session_id': self.anonymous_session_id,
            'session_id': self.session_id,
            'activity_id': self.activity_id,
            'activity_type': self.activity_type,
            'was_skipped': self.was_skipped,
            'feedback_type': self.feedback_type,
            'feedback_executed': self.feedback_executed,
            'presented_at': self.presented_at.isoformat(),
            'theme_tags': self.theme_tags
        }
