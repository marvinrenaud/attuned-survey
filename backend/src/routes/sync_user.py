from flask import Blueprint, jsonify, current_app
from ..db.repository import sync_user_anatomy_to_profile

sync_user_bp = Blueprint('sync_user', __name__, url_prefix='/api/users')

@sync_user_bp.route('/<user_id>/sync', methods=['POST'])
def sync_user(user_id):
    """
    Sync user data (specifically anatomy) to their profile.
    This endpoint is intended to be called by a database trigger
    when the users table is updated (e.g., anatomy change).
    """
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
        return jsonify({'error': str(e)}), 500
