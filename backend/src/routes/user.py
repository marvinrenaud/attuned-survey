from flask import Blueprint, jsonify, request, abort
from ..models.user import User
from ..middleware.auth import token_required
from ..extensions import db
import uuid

user_bp = Blueprint('user', __name__)

# Endpoints 'get_users' and 'create_user' have been removed for security.


@user_bp.route('/users/<user_id>', methods=['GET'])
@token_required
def get_user(current_user_id, user_id):
    """Get user by UUID (changed from integer ID)."""
    if str(current_user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        uid_obj = uuid.UUID(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid ID'}), 400

    user = User.query.filter_by(id=uid_obj).first_or_404()
    return jsonify(user.to_dict())

@user_bp.route('/users/<user_id>', methods=['PUT'])
@token_required
def update_user(current_user_id, user_id):
    """
    Update user details.
    Note: 'username' is mapped to 'display_name' for backward compatibility.
    """
    if str(current_user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        uid_obj = uuid.UUID(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid ID'}), 400

    user = User.query.filter_by(id=uid_obj).first_or_404()
    data = request.json
    
    # Support both old 'username' and new 'display_name' fields
    if 'username' in data:
        user.display_name = data['username']
    if 'display_name' in data:
        user.display_name = data['display_name']
    
    if 'email' in data:
        user.email = data['email']
    
    if 'demographics' in data:
        user.demographics = data['demographics']
    
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user_id, user_id):
    """Delete user by UUID (changed from integer ID)."""
    if str(current_user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        uid_obj = uuid.UUID(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid ID'}), 400

    user = User.query.filter_by(id=uid_obj).first_or_404()
    db.session.delete(user)
    db.session.commit()
    return '', 204
