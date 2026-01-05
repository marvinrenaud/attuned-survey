
import logging
from datetime import datetime, timedelta
from sqlalchemy import or_

from ..extensions import db
from ..models.partner import PartnerConnection
from ..models.session import Session
from ..models.survey import SurveySubmission, SurveyProgress

logger = logging.getLogger(__name__)

class CleanupService:
    """Service to handle periodic cleanup of stale data."""
    
    @staticmethod
    def cleanup_pending_connections() -> int:
        """Expire 'pending' connections older than 24 hours (or expiration time)."""
        try:
            now = datetime.utcnow()
            count = PartnerConnection.query.filter(
                PartnerConnection.status == 'pending',
                PartnerConnection.expires_at < now
            ).update(
                {PartnerConnection.status: 'expired'},
                synchronize_session=False
            )
            db.session.commit()
            return count
        except Exception as e:
            logger.error(f"Error cleaning up pending connections: {e}")
            db.session.rollback()
            return 0

    @staticmethod
    def cleanup_stale_sessions() -> int:
        """Abandon 'active' sessions older than 7 days."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=7)
            count = Session.query.filter(
                Session.status == 'active',
                Session.created_at < cutoff
            ).update(
                {Session.status: 'abandoned'},
                synchronize_session=False
            )
            db.session.commit()
            return count
        except Exception as e:
            logger.error(f"Error cleaning up stale sessions: {e}")
            db.session.rollback()
            return 0

    @staticmethod
    def cleanup_abandoned_surveys() -> int:
        """Mark 'in_progress' surveys older than 30 days as abandoned."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=30)
            
            count = SurveyProgress.query.filter(
                SurveyProgress.status == 'in_progress',
                SurveyProgress.last_saved_at < cutoff
            ).update(
                {SurveyProgress.status: 'abandoned'},
                synchronize_session=False
            )
            
            db.session.commit()
            return count
        except Exception as e:
            logger.error(f"Error cleaning up surveys: {e}")
            db.session.rollback()
            return 0

    @staticmethod
    def run_all():
        """Run all cleanup tasks and log results."""
        logger.info("Starting cleanup job...")
        
        expired_conn = CleanupService.cleanup_pending_connections()
        abandoned_sess = CleanupService.cleanup_stale_sessions()
        abandoned_surv = CleanupService.cleanup_abandoned_surveys()
        
        logger.info(f"Cleanup complete: {expired_conn} connections expired, {abandoned_sess} sessions abandoned, {abandoned_surv} surveys marked abandoned")
