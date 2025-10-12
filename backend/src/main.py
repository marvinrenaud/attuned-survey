# backend/src/main.py
import os
from datetime import datetime

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

# --- Database config (Render injects DATABASE_URL) ---
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL env var is required")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class SurveySubmission(db.Model):
    __tablename__ = "survey_submissions"
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.String(128), unique=True, nullable=False)
    respondent_id = db.Column(db.String(128), index=True, nullable=True)
    payload_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class SurveyBaseline(db.Model):
    __tablename__ = "survey_baseline"
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.String(128), nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

# Create the table(s) on boot (simple & fine for now)
with app.app_context():
    db.create_all()

# --- Routes ---
from .routes.survey import bp as survey_bp  # noqa: E402

app.register_blueprint(survey_bp)
