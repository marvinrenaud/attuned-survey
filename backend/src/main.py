# backend/src/main.py
import os

from flask import Flask
from flask_cors import CORS

from .extensions import db
from .models.survey import SurveyBaseline, SurveySubmission


def create_app() -> Flask:
    """Application factory so routes can import models without circular deps."""

    app = Flask(__name__)
    CORS(app)

    # --- Database config (Render injects DATABASE_URL) ---
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL env var is required")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        # Create the table(s) on boot (simple & fine for now)
        db.create_all()

    # --- Routes ---
    from .routes.survey import bp as survey_bp  # noqa: WPS433 (local import)

    app.register_blueprint(survey_bp)

    return app


app = create_app()


__all__ = [
    "app",
    "db",
    "SurveyBaseline",
    "SurveySubmission",
]
