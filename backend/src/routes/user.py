from flask import Blueprint, jsonify, request
from ..models.user import User
from ..extensions import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    """
    Legacy endpoint - kept for backward compatibility.
    For new registrations, use /api/auth/register instead.
    """
    data = request.json
    
    # Map old 'username' field to new 'display_name' field
    display_name = data.get('username') or data.get('display_name')
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    user = User(
        id=data.get('id'),  # Must be provided (UUID from Supabase Auth)
        email=email,
        display_name=display_name,
        auth_provider=data.get('auth_provider', 'email')
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by UUID (changed from integer ID)."""
    user = User.query.filter_by(id=user_id).first_or_404()
    return jsonify(user.to_dict())

@user_bp.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update user details.
    Note: 'username' is mapped to 'display_name' for backward compatibility.
    """
    user = User.query.filter_by(id=user_id).first_or_404()
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
def delete_user(user_id):
    """Delete user by UUID (changed from integer ID)."""
    user = User.query.filter_by(id=user_id).first_or_404()
    db.session.delete(user)
    db.session.commit()
    return '', 204
