"""Database models for survey data."""
from datetime import datetime

from ..extensions import db


class SurveySubmission(db.Model):
    __tablename__ = "survey_submissions"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.String(128), unique=True, nullable=False)
    respondent_id = db.Column(db.String(128), index=True, nullable=True)
    name = db.Column(db.String(256), nullable=True)
    sex = db.Column(db.String(32), nullable=True)
    sexual_orientation = db.Column(db.String(64), nullable=True)
    payload_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class SurveyBaseline(db.Model):
    __tablename__ = "survey_baseline"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.String(128), nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
