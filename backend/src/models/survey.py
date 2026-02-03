"""Database models for survey data."""
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from .guid import GUID
from ..extensions import db


class SurveySubmission(db.Model):
    __tablename__ = "survey_submissions"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.String(128), unique=True, nullable=False)
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    respondent_id = db.Column(db.String(128), index=True, nullable=True)
    name = db.Column(db.String(256), nullable=True)
    sex = db.Column(db.String(32), nullable=True)
    sexual_orientation = db.Column(db.String(64), nullable=True)
    survey_version = db.Column(db.String(16), nullable=True)
    survey_progress_id = db.Column(db.Integer, db.ForeignKey('survey_progress.id', ondelete='SET NULL'), nullable=True)
    payload_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship to User
    user = db.relationship("User", backref=db.backref("submission", uselist=False))


class SurveyBaseline(db.Model):
    __tablename__ = "survey_baseline"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.String(128), nullable=True)
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
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
    question_pre_prompt = db.Column(db.Text, nullable=True)  # Introductory text/question
    options = db.Column(db.Text, nullable=True)  # e.g., "1=Strongly disagree ... 7=Strongly agree"
    maps = db.Column(db.JSON, nullable=True)  # Metadata: {"factor":"SE"}, {"category":"physical_touch",...}
    display_order = db.Column(db.Integer, nullable=True)  # Order within chapter
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # Can disable questions
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint('survey_version', 'question_id', name='uq_survey_questions_version_id'),
    )


class SurveyProgress(db.Model):
    """Tracks in-progress survey drafts."""
    __tablename__ = "survey_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(GUID(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    anonymous_session_id = db.Column(db.Text, nullable=True, index=True)
    survey_version = db.Column(db.Text, nullable=False, default='0.4')
    status = db.Column(db.Enum('in_progress', 'completed', 'abandoned', name='survey_status_enum'), nullable=False, default='in_progress')
    current_question = db.Column(db.Text, nullable=True)
    completion_percentage = db.Column(db.Integer, nullable=False, default=0)
    answers = db.Column(db.JSON, nullable=False, default=dict)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_saved_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    current_question_index = db.Column(db.Integer, nullable=True)

    # Relationships
    # Note: SurveySubmission has a FK to this table, but we don't strictly need the backref here yet.
