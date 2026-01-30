import os
from flask import Blueprint, jsonify
from ..middleware.auth import token_required
from ..services.config_service import refresh_cache
import logging

logger = logging.getLogger(__name__)

system_admin_bp = Blueprint('system_admin', __name__, url_prefix='/api/system-admin')


def is_admin(user_id):
    """
    Check if user is an admin based on ADMIN_USER_IDS env var.

    Returns True if user_id is in the comma-separated list of admin UUIDs.
    """
    admin_ids = os.environ.get('ADMIN_USER_IDS', '').split(',')
    return str(user_id) in [aid.strip() for aid in admin_ids if aid.strip()]


@system_admin_bp.route('/cache/refresh', methods=['POST'])
@token_required
def trigger_cache_refresh(current_user_id):
    """
    Force a reload of the configuration cache.

    Security: Requires admin role (user ID in ADMIN_USER_IDS env var).
    """
    # Admin check
    if not is_admin(current_user_id):
        logger.warning(f"Non-admin user {current_user_id} attempted cache refresh")
        return jsonify({"error": "Forbidden"}), 403

    logger.info(f"Config cache refresh triggered by admin user {current_user_id}")

    try:
        refresh_cache()
        return jsonify({
            "success": True,
            "message": "Configuration cache refreshed successfully"
        }), 200
    except Exception as e:
        logger.error(f"Failed to refresh cache: {e}")
        return jsonify({"success": False, "error": "Cache refresh failed"}), 500
