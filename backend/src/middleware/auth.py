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
