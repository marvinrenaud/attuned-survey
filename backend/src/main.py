# backend/src/main.py
# IMPROVED VERSION with proper connection pooling and error handling

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Load environment variables from .env file
# Try loading from backend/ first, then project root
backend_env = Path(__file__).parent.parent / '.env'
if backend_env.exists():
    load_dotenv(dotenv_path=backend_env)
else:
    # Fallback to project root
    root_env = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(dotenv_path=root_env)

from flask import Flask
from flask_cors import CORS
from sqlalchemy import text
from flask_limiter import Limiter

from .extensions import db, limiter
from .logging_config import (
    configure_logging, 
    request_context_middleware, 
    log_request_complete
)
from .models.survey import SurveyBaseline, SurveySubmission
from .models.profile import Profile
from .models.session import Session
from .models.activity import Activity
from .models.session_activity import SessionActivity
from .models.compatibility import Compatibility
from .models.user import User
from .models.influencer import Influencer
from .models.promo_code import PromoCode
from .models.promo_redemption import PromoRedemption


def create_app() -> Flask:
    """Application factory so routes can import models without circular deps."""

    app = Flask(__name__)
    CORS(app, origins=[
        "https://getattuned.app",
        "https://app.getattuned.app",
        "https://attuned.flutterflow.app",  # Explicit FF web app origin
        "https://*.flutterflow.app",  # For other FF preview/test modes
        "http://localhost:*"  # For local development
    ])

    # --- Database config (Render injects DATABASE_URL) ---
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL env var is required")
    
    # Fix for Render/Heroku DATABASE_URL format (postgres:// -> postgresql://)
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        # We can't use the structlog logger here yet as it's not configured
        # But we can rely on standard logging or just print for this critical early config
        print("Converted DATABASE_URL from postgres:// to postgresql+psycopg://")
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        print("Converted DATABASE_URL from postgresql:// to postgresql+psycopg://")
    
    # Ensure SSL mode is set
    if "sslmode=" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}sslmode=require"
        print("Added sslmode=require to DATABASE_URL")
    
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB

    
    # Connection pooling configuration
    # Only apply PostgreSQL-specific settings for PostgreSQL databases
    # Connection pooling configuration
    # Only apply PostgreSQL-specific settings for PostgreSQL databases
    if db_url.startswith("postgresql") and "psycopg" in db_url:
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

    
    # Configure structured logging
    logger = configure_logging(app)
    
    # Add request lifecycle hooks
    @app.before_request
    def before_request():
        request_context_middleware()
    
    @app.after_request
    def after_request(response):
        return log_request_complete(response)

    
    # Rate Limiting Config
    app.config["RATELIMIT_DEFAULT"] = "2000 per day;500 per hour"
    app.config["RATELIMIT_STORAGE_URI"] = "memory://"
    
    db.init_app(app)
    limiter.init_app(app)

    with app.app_context():
        try:
             # Detect if using Supabase pooler (PgBouncer doesn't allow DDL)
            is_pooler = 'pooler.supabase.com' in db_url or "supavisor" in db_url
            
            if is_pooler:
                logger.info("connection_pooler_detected", skip_ddl=True)
                logger.info("ddl_skipped_pooler_mode")
            
            # Test basic connectivity
            logger.info("db_connection_attempt")
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            logger.info("db_connection_success")
            
            # Only run DDL if NOT using pooler
            if not is_pooler:
                logger.info("starting_ddl_operations")
                
                # Create tables
                try:
                    db.create_all()
                    logger.info("tables_verified")
                except Exception as table_error:
                    logger.warning("table_creation_failed", error=str(table_error))
                
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
                    logger.info("survey_columns_verified")
                except Exception as col_error:
                    logger.warning("column_verification_failed", error=str(col_error))
                    db.session.rollback()
            else:
                logger.info("pooler_mode_active")
                
        except Exception as e:
            logger.error("db_initialization_failed", error=str(e))
            logger.error("app_starting_with_db_issues")
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
        from .routes.profile_ui import profile_ui_bp
        from .routes.gameplay import gameplay_bp
        from .routes.system_admin import system_admin_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(partners_bp)
        app.register_blueprint(subscriptions_bp)
        app.register_blueprint(profile_sharing_bp)
        app.register_blueprint(process_submission_bp)
        app.register_blueprint(sync_user_bp)
        app.register_blueprint(profile_ui_bp)
        app.register_blueprint(gameplay_bp)
        app.register_blueprint(system_admin_bp)
        
        from .routes.compatibility import compatibility_bp
        app.register_blueprint(compatibility_bp)
        
        from .routes.survey_submit import survey_submit_bp
        app.register_blueprint(survey_submit_bp)
        
        from .routes.notifications import notifications_bp
        app.register_blueprint(notifications_bp)
        
        # Initialize Firebase for push notifications
        from .firebase_config import initialize_firebase
        if initialize_firebase():
            logger.info("firebase_initialized_for_push_notifications")
        else:
            logger.warning("firebase_initialization_failed_push_notifications_disabled")
        
        env = os.environ.get("FLASK_ENV", "production")
        is_prod = env == "production"
        if is_prod:
           logger.info("mvp_routes_registered", env=env)
    except Exception as e:
        logger.warning("mvp_routes_registration_failed", error=str(e))

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
