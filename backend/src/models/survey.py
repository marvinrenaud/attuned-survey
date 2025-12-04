"""Database models for survey data."""
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

from ..extensions import db


class SurveySubmission(db.Model):
    __tablename__ = "survey_submissions"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.String(128), unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    respondent_id = db.Column(db.String(128), index=True, nullable=True)
    name = db.Column(db.String(256), nullable=True)
    sex = db.Column(db.String(32), nullable=True)
    sexual_orientation = db.Column(db.String(64), nullable=True)
    version = db.Column(db.String(16), nullable=True)
    payload_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class SurveyBaseline(db.Model):
    __tablename__ = "survey_baseline"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.String(128), nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class SurveyQuestion(db.Model):
    """Survey question definitions."""
    __tablename__ = "survey_questions"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.String(32), nullable=False)  # e.g., "A1", "B1a", "C1"
    survey_version = db.Column(db.String(16), nullable=False, default='0.4')  # Version of survey
    chapter = db.Column(db.String(128), nullable=False)  # e.g., "Arousal & Power", "Physical Touch"
    question_type = db.Column(db.String(32), nullable=False)  # e.g., "likert7", "chooseYMN"
    prompt = db.Column(db.Text, nullable=False)  # The actual question text
    options = db.Column(db.Text, nullable=True)  # e.g., "1=Strongly disagree ... 7=Strongly agree"
    maps = db.Column(db.JSON, nullable=True)  # Metadata: {"factor":"SE"}, {"category":"physical_touch",...}
    display_order = db.Column(db.Integer, nullable=True)  # Order within chapter
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # Can disable questions
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint('survey_version', 'question_id', name='uq_survey_questions_version_id'),
    )
