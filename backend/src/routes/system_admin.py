from flask import Blueprint, jsonify
from ..middleware.auth import token_required
from ..services.config_service import refresh_cache
import logging

logger = logging.getLogger(__name__)

system_admin_bp = Blueprint('system_admin', __name__, url_prefix='/api/system-admin')

@system_admin_bp.route('/cache/refresh', methods=['POST'])
@token_required
def trigger_cache_refresh(current_user_id):
    """
    Force a reload of the configuration cache.
    TODO: Add admin role check when role system is mature.
    """
    # For MVP, we'll log who did it. 
    # Real admin check would go here: if not is_admin(current_user_id): return 403
    logger.info(f"Config cache refresh triggered by user {current_user_id}")
    
    try:
        refresh_cache()
        return jsonify({
            "success": True, 
            "message": "Configuration cache refreshed successfully"
        }), 200
    except Exception as e:
        logger.error(f"Failed to refresh cache: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
