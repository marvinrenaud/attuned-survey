"""
Activity limit service - shared logic for checking and incrementing
activity counters across lifetime/weekly/daily modes.

The mode is controlled by the `free_tier_limit_mode` key in app_config:
  - 'lifetime': count never resets (original behavior)
  - 'weekly': count resets every 7 days (default)
  - 'daily': count resets every 24 hours

Lazy auto-reset: counters are reset on read if the window has expired.
Belt-and-suspenders: CleanupService also bulk-resets expired counters daily.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import uuid
import logging

from ..extensions import db
from ..models.user import User
from ..services.config_service import get_config, get_config_int
from sqlalchemy import text

logger = logging.getLogger(__name__)


def get_limit_mode() -> str:
    """Get the current activity limit mode from app_config."""
    return get_config('free_tier_limit_mode', 'weekly')


def get_limit_value() -> int:
    """Get the current activity limit number from app_config."""
    return get_config_int('free_tier_activity_limit', 10)


def get_active_count_and_reset(user: User, mode: str) -> Tuple[int, Optional[datetime]]:
    """
    Get the current activity count for the given mode, auto-resetting if expired.

    Args:
        user: The User ORM object
        mode: 'lifetime', 'weekly', or 'daily'

    Returns:
        (count, resets_at) where resets_at is None for lifetime mode.
        resets_at is the datetime when the counter will next reset.
    """
    now = datetime.now(timezone.utc)

    if mode == 'lifetime':
        return (user.lifetime_activity_count or 0, None)

    elif mode == 'weekly':
        reset_at = user.weekly_activity_reset_at
        # Ensure timezone-aware comparison (PostgreSQL returns aware, SQLite returns naive)
        if reset_at is not None and reset_at.tzinfo is None:
            reset_at = reset_at.replace(tzinfo=timezone.utc)
        if reset_at is None or (now - reset_at).total_seconds() >= 7 * 24 * 3600:
            user.weekly_activity_count = 0
            user.weekly_activity_reset_at = now
            db.session.flush()
            reset_at = now
        next_reset = reset_at + timedelta(days=7)
        return (user.weekly_activity_count or 0, next_reset)

    elif mode == 'daily':
        reset_at = user.daily_activity_reset_at
        if reset_at is not None and reset_at.tzinfo is None:
            reset_at = reset_at.replace(tzinfo=timezone.utc)
        if reset_at is None or (now - reset_at).total_seconds() >= 24 * 3600:
            user.daily_activity_count = 0
            user.daily_activity_reset_at = now
            db.session.flush()
            reset_at = now
        next_reset = reset_at + timedelta(days=1)
        return (user.daily_activity_count or 0, next_reset)

    # Unknown mode: fall back to lifetime (safe default)
    logger.warning(f"Unknown limit mode '{mode}', falling back to lifetime")
    return (user.lifetime_activity_count or 0, None)


def increment_activity_count(user: User, mode: str):
    """
    Increment the correct activity counter for the user.
    Always increments lifetime_activity_count as a permanent ledger.

    Does NOT commit -- caller is responsible for db.session.commit().
    """
    # Always increment lifetime as permanent ledger
    user.lifetime_activity_count = (user.lifetime_activity_count or 0) + 1

    if mode == 'weekly':
        get_active_count_and_reset(user, mode)  # auto-reset if needed
        user.weekly_activity_count = (user.weekly_activity_count or 0) + 1
    elif mode == 'daily':
        get_active_count_and_reset(user, mode)  # auto-reset if needed
        user.daily_activity_count = (user.daily_activity_count or 0) + 1
    # 'lifetime' mode: only lifetime_activity_count incremented (above)


def get_anonymous_usage(anon_id: str, mode: str = 'weekly') -> int:
    """Count activities presented to anonymous session based on limit mode."""
    if mode == 'lifetime':
        sql = text("""
            SELECT COUNT(*) FROM user_activity_history
            WHERE anonymous_session_id = :anon_id
        """)
        result = db.session.execute(sql, {"anon_id": anon_id}).scalar()
    elif mode == 'daily':
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        sql = text("""
            SELECT COUNT(*) FROM user_activity_history
            WHERE anonymous_session_id = :anon_id
            AND presented_at > :cutoff
        """)
        result = db.session.execute(sql, {"anon_id": anon_id, "cutoff": cutoff}).scalar()
    else:  # 'weekly' (default)
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        sql = text("""
            SELECT COUNT(*) FROM user_activity_history
            WHERE anonymous_session_id = :anon_id
            AND presented_at > :cutoff
        """)
        result = db.session.execute(sql, {"anon_id": anon_id, "cutoff": cutoff}).scalar()

    return result or 0


def check_activity_limit(
    user_id: Optional[str] = None,
    anonymous_session_id: Optional[str] = None
) -> dict:
    """
    Check if user (auth or anon) has reached activity limit based on current mode.

    Returns dict with keys:
        - limit_reached (bool)
        - remaining (int, -1 for premium)
        - is_capped (bool)
        - used (int)
        - limit (int)
        - limit_mode (str): 'LIFETIME', 'WEEKLY', or 'DAILY'
        - resets_at (str, ISO format): only present for weekly/daily modes
    """
    limit = get_limit_value()
    mode = get_limit_mode()

    # 1. Authenticated User
    if user_id:
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return {"error": "Invalid User ID"}

        user = User.query.get(user_id)
        if not user:
            return {"error": "User not found"}

        if user.subscription_tier == 'premium':
            return {
                "limit_reached": False,
                "remaining": -1,
                "is_capped": False,
                "limit_mode": mode.upper(),
            }

        used, resets_at = get_active_count_and_reset(user, mode)

        result = {
            "limit_reached": used >= limit,
            "remaining": max(0, limit - used),
            "is_capped": True,
            "used": used,
            "limit": limit,
            "limit_mode": mode.upper(),
        }
        if resets_at is not None:
            result["resets_at"] = resets_at.isoformat()
        return result

    # 2. Anonymous User
    if anonymous_session_id:
        used_count = get_anonymous_usage(anonymous_session_id, mode)
        return {
            "limit_reached": used_count >= limit,
            "remaining": max(0, limit - used_count),
            "is_capped": True,
            "used": used_count,
            "limit": limit,
            "limit_mode": mode.upper(),
        }

    return {"error": "No identity provided"}
