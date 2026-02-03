
import logging
from datetime import datetime, timedelta, timezone
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
            now = datetime.now(timezone.utc)
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
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
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
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            
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
    def reset_expired_weekly_counters() -> int:
        """Reset weekly_activity_count for free users whose 7-day window has expired.
        Belt-and-suspenders backup for lazy app-level reset in activity_limit_service."""
        try:
            from ..models.user import User
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            count = User.query.filter(
                User.subscription_tier == 'free',
                User.weekly_activity_reset_at < cutoff
            ).update(
                {
                    User.weekly_activity_count: 0,
                    User.weekly_activity_reset_at: datetime.now(timezone.utc)
                },
                synchronize_session=False
            )
            db.session.commit()
            return count
        except Exception as e:
            logger.error(f"Error resetting weekly counters: {e}")
            db.session.rollback()
            return 0

    @staticmethod
    def run_all():
        """Run all cleanup tasks and log results."""
        logger.info("Starting cleanup job...")

        expired_conn = CleanupService.cleanup_pending_connections()
        abandoned_sess = CleanupService.cleanup_stale_sessions()
        abandoned_surv = CleanupService.cleanup_abandoned_surveys()
        weekly_resets = CleanupService.reset_expired_weekly_counters()

        logger.info(
            f"Cleanup complete: {expired_conn} connections expired, "
            f"{abandoned_sess} sessions abandoned, "
            f"{abandoned_surv} surveys marked abandoned, "
            f"{weekly_resets} weekly counters reset"
        )
