# backend/src/main.py
# IMPROVED VERSION with proper connection pooling and error handling

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from flask import Flask
from flask_cors import CORS
from sqlalchemy import text

from .extensions import db
from .models.survey import SurveyBaseline, SurveySubmission
from .models.profile import Profile
from .models.session import Session
from .models.activity import Activity
from .models.session_activity import SessionActivity
from .models.compatibility import Compatibility
from .models.user import User


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
    # Only apply PostgreSQL-specific settings for PostgreSQL databases
    if db_url.startswith("postgresql://"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_size": 10,             # Increased pool size
            "pool_recycle": 60,          # Recycle connections after 1 minute (Supabase closes idle conns fast)
            "pool_pre_ping": True,       # Verify connections before using them
            "max_overflow": 5,           # Allow extra connections when pool full
            "pool_timeout": 30,          # Wait up to 30 seconds for a connection
            "connect_args": {
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            }
        }
    else:
        # For SQLite and other databases, use minimal configuration
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,       # Verify connections before using them
        }

    # Enable SQLAlchemy logging in development
    if os.environ.get("FLASK_ENV") == "development":
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    db.init_app(app)

    with app.app_context():
        try:
            # Detect if using Supabase pooler (PgBouncer doesn't allow DDL)
            is_pooler = 'pooler.supabase.com' in db_url
            
            if is_pooler:
                app.logger.info("🔗 Detected Supabase connection pooler - skipping DDL operations")
                app.logger.info("   (Tables should already exist; DDL not allowed through PgBouncer)")
            
            # Test basic connectivity
            app.logger.info("Attempting database connection...")
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            app.logger.info("✅ Database connection successful")
            
            # Only run DDL if NOT using pooler
            if not is_pooler:
                app.logger.info("Running DDL operations (create tables, add columns)...")
                
                # Create tables
                try:
                    db.create_all()
                    app.logger.info("✅ Tables created/verified")
                except Exception as table_error:
                    app.logger.warning(f"⚠️ Table creation failed: {table_error}")
                
                # Add missing columns (for backward compatibility)
                try:
                    db.session.execute(text(
                        """
                        ALTER TABLE survey_submissions
                        ADD COLUMN IF NOT EXISTS name VARCHAR(256);
                        """
                    ))
                    db.session.execute(text(
                        """
                        ALTER TABLE survey_submissions
                        ADD COLUMN IF NOT EXISTS sex VARCHAR(32);
                        """
                    ))
                    db.session.execute(text(
                        """
                        ALTER TABLE survey_submissions
                        ADD COLUMN IF NOT EXISTS sexual_orientation VARCHAR(64);
                        """
                    ))
                    db.session.commit()
                    app.logger.info("✅ Verified survey_submissions columns")
                except Exception as col_error:
                    app.logger.warning(f"⚠️ Column verification failed: {col_error}")
                    db.session.rollback()
            else:
                app.logger.info("✅ Pooler mode - assuming tables and columns already exist")
                
        except Exception as e:
            app.logger.error(f"❌ Database initialization failed: {e}")
            app.logger.error("App will start but database operations may fail")
            # Don't raise - allow app to start even if DB has issues

    # --- Routes ---
    from .routes.survey import bp as survey_bp  # noqa: WPS433 (local import)
    from .routes.recommendations import bp as recommendations_bp  # noqa: WPS433 (local import)
    from .routes.user import user_bp  # noqa: WPS433 (local import)
    
    # New MVP routes
    try:
        from .routes.auth import auth_bp  # noqa: WPS433
        from .routes.partners import partners_bp  # noqa: WPS433
        from .routes.subscriptions import subscriptions_bp  # noqa: WPS433
        from .routes.profile_sharing import profile_sharing_bp
        from .routes.process_submission import process_submission_bp
        from .routes.sync_user import sync_user_bp  # noqa: WPS433
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(partners_bp)
        app.register_blueprint(subscriptions_bp)
        app.register_blueprint(profile_sharing_bp)
        app.register_blueprint(process_submission_bp)
        app.register_blueprint(sync_user_bp)
        app.logger.info("✅ MVP routes registered")
    except Exception as e:
        app.logger.warning(f"⚠️ Could not register MVP routes: {e}")

    app.register_blueprint(survey_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(user_bp)

    return app


app = create_app()


__all__ = [
    "app",
    "db",
    "User",
    "SurveyBaseline",
    "SurveySubmission",
    "Profile",
    "Session",
    "Activity",
    "SessionActivity",
    "Compatibility",
]
