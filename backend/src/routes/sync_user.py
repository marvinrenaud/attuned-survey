import os
from flask import Blueprint, jsonify, request, current_app
from ..db.repository import sync_user_anatomy_to_profile
from ..middleware.auth import token_required

sync_user_bp = Blueprint('sync_user', __name__, url_prefix='/api/users')


def verify_internal_webhook_auth():
    """
    Verify internal webhook authorization.

    Returns:
        True if valid internal webhook secret provided
        False if invalid secret provided
        None if no secret configured (fallback to user auth)
    """
    secret = os.environ.get('INTERNAL_WEBHOOK_SECRET')
    if not secret:
        return None  # No secret configured, signal to use user auth

    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False

    token = auth_header[7:]
    return token == secret


@sync_user_bp.route('/<user_id>/sync', methods=['POST'])
def sync_user(user_id):
    """
    Sync user data (specifically anatomy) to their profile.
    This endpoint is intended to be called by a database trigger
    when the users table is updated (e.g., anatomy change).

    Security: Requires either INTERNAL_WEBHOOK_SECRET or valid user JWT.
    """
    # Check internal webhook auth first
    auth_result = verify_internal_webhook_auth()

    if auth_result is False:
        return jsonify({'error': 'Unauthorized'}), 401

    if auth_result is None:
        # No internal secret configured - this endpoint should not be publicly accessible
        # without configuration. Return 401 to prevent unauthorized access.
        current_app.logger.warning(
            f"sync_user called without INTERNAL_WEBHOOK_SECRET configured for user {user_id}"
        )
        return jsonify({'error': 'Unauthorized - endpoint not configured'}), 401

    # auth_result is True - internal webhook auth passed
    try:
        current_app.logger.info(f"Syncing user: {user_id}")

        success = sync_user_anatomy_to_profile(user_id)

        if success:
            return jsonify({'message': 'User synced successfully'}), 200
        else:
            # This might happen if profile doesn't exist yet, which is fine
            return jsonify({'message': 'Sync attempted, but no profile found or user not found'}), 200

    except Exception as e:
        current_app.logger.error(f"Error syncing user {user_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
