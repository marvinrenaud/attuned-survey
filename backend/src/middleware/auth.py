"""
Authentication middleware for validating Supabase JWT tokens.
"""
import os
import jwt
from functools import wraps
from flask import request, jsonify, current_app

import logging

logger = logging.getLogger(__name__)

def get_jwt_secret():
    """Retrieve the Supabase JWT secret from environment variables."""
    secret = os.environ.get('SUPABASE_JWT_SECRET')
    if not secret:
        # Log a warning to help debugging
        logger.error("SUPABASE_JWT_SECRET is not set")
        raise ValueError("SUPABASE_JWT_SECRET environment variable is not set.")
    return secret

def token_required(f):
    """
    Decorator that requires a valid JWT token for route access.
    Passes 'current_user_id' (UUID) to the decorated function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 1. Extract Token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        
        if not token:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Missing Authorization Header'
            }), 401
        
        try:
            # 2. Verify Token
            # Supabase tokens use HMAC-SHA256 (HS256) and audience="authenticated"
            payload = jwt.decode(
                token,
                get_jwt_secret(),
                algorithms=["HS256"],
                audience="authenticated"
            )
            
            # 3. Extract User ID
            current_user_id = payload.get('sub')
            if not current_user_id:
                return jsonify({'error': 'Invalid token', 'message': 'No user ID found in token'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired', 'message': 'Please log in again'}), 401
        except jwt.InvalidAudienceError:
            return jsonify({'error': 'Invalid token', 'message': 'Invalid audience'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'error': 'Invalid token', 'message': str(e)}), 401
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Authentication failed', 'message': str(e)}), 500

        # 4. Pass User ID to Route
        return f(current_user_id, *args, **kwargs)
    
    return decorated

def optional_token(f):
    """
    Decorator for optional authentication.
    Passes 'current_user_id' (UUID or None) to the decorated function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user_id = None
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]

        if token:
            try:
                payload = jwt.decode(
                    token,
                    get_jwt_secret(),
                    algorithms=["HS256"],
                    audience="authenticated"
                )
                current_user_id = payload.get('sub')
            except Exception:
                # Ignore validation errors for optional auth
                pass

        return f(current_user_id, *args, **kwargs)

    return decorated


# =============================================================================
# Security Helper Functions
# =============================================================================

def is_admin_user(user_id: str) -> bool:
    """
    Check if a user is an admin based on ADMIN_USER_IDS environment variable.

    Args:
        user_id: The user's UUID as a string

    Returns:
        True if user_id is in the comma-separated ADMIN_USER_IDS list
    """
    admin_ids = os.environ.get('ADMIN_USER_IDS', '').split(',')
    return str(user_id) in [aid.strip() for aid in admin_ids if aid.strip()]


def verify_internal_webhook_secret() -> bool:
    """
    Verify the internal webhook secret from the X-Internal-Secret header.
    Used for endpoints called by database triggers.

    Returns:
        True if valid secret provided, False otherwise
    """
    secret = os.environ.get('INTERNAL_WEBHOOK_SECRET')
    if not secret:
        logger.warning("INTERNAL_WEBHOOK_SECRET not configured")
        return False

    provided_secret = request.headers.get('X-Internal-Secret', '')
    return provided_secret == secret


def internal_webhook_required(f):
    """
    Decorator for endpoints called by database triggers.
    Requires X-Internal-Secret header to match INTERNAL_WEBHOOK_SECRET env var.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not verify_internal_webhook_secret():
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """
    Decorator that requires the user to be an admin.
    Must be used AFTER @token_required decorator.

    Usage:
        @bp.route('/admin-only')
        @token_required
        @require_admin
        def admin_endpoint(current_user_id):
            ...
    """
    @wraps(f)
    def decorated(current_user_id, *args, **kwargs):
        if not is_admin_user(current_user_id):
            logger.warning(f"Non-admin user {current_user_id} attempted admin action")
            return jsonify({'error': 'Admin access required'}), 403
        return f(current_user_id, *args, **kwargs)
    return decorated


def has_partner_relationship(user_a_id, user_b_id) -> bool:
    """
    Check if two users have an accepted partner relationship.
    Checks both PartnerConnection (accepted) and RememberedPartner tables.

    Args:
        user_a_id: First user's UUID (string or UUID object)
        user_b_id: Second user's UUID (string or UUID object)

    Returns:
        True if users have an accepted connection or remembered partner relationship
    """
    import uuid
    from sqlalchemy import or_
    from ..models.partner import PartnerConnection, RememberedPartner

    # Convert to UUID objects if strings
    try:
        a_uuid = uuid.UUID(str(user_a_id))
        b_uuid = uuid.UUID(str(user_b_id))
    except ValueError:
        return False

    # Check for accepted PartnerConnection (either direction)
    connection = PartnerConnection.query.filter(
        or_(
            (PartnerConnection.requester_user_id == a_uuid) &
            (PartnerConnection.recipient_user_id == b_uuid) &
            (PartnerConnection.status == 'accepted'),
            (PartnerConnection.requester_user_id == b_uuid) &
            (PartnerConnection.recipient_user_id == a_uuid) &
            (PartnerConnection.status == 'accepted')
        )
    ).first()

    if connection:
        return True

    # Check RememberedPartner (either direction)
    remembered = RememberedPartner.query.filter(
        or_(
            (RememberedPartner.user_id == a_uuid) &
            (RememberedPartner.partner_user_id == b_uuid),
            (RememberedPartner.user_id == b_uuid) &
            (RememberedPartner.partner_user_id == a_uuid)
        )
    ).first()

    return remembered is not None
