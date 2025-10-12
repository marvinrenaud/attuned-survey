# backend/src/main.py
# IMPROVED VERSION with proper connection pooling and error handling

import os
import logging

from flask import Flask
from flask_cors import CORS
from sqlalchemy import text

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
    
    # Fix for Render/Heroku DATABASE_URL format (postgres:// -> postgresql://)
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        app.logger.info("Converted DATABASE_URL from postgres:// to postgresql://")
    
    # Ensure SSL mode is set
    if "sslmode=" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}sslmode=require"
        app.logger.info("Added sslmode=require to DATABASE_URL")
    
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Connection pooling configuration
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 5,              # Number of connections to maintain
        "pool_recycle": 300,         # Recycle connections after 5 minutes
        "pool_pre_ping": True,       # Verify connections before using them
        "max_overflow": 2,           # Allow 2 additional connections when pool is full
        "pool_timeout": 30,          # Wait up to 30 seconds for a connection
        "connect_args": {
            "sslmode": "require",    # Require SSL connection
            "connect_timeout": 10,   # Connection timeout in seconds
        }
    }

    # Enable SQLAlchemy logging in development
    if os.environ.get("FLASK_ENV") == "development":
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    db.init_app(app)

    with app.app_context():
        try:
            # Create the table(s) on boot (simple & fine for now)
            db.create_all()
            
            # Test database connection
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            app.logger.info("✅ Database connection successful")
        except Exception as e:
            app.logger.error(f"❌ Database connection failed: {e}")
            raise

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
