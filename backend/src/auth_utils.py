import json
import base64
from flask import request, current_app

def get_current_user_id():
    """
    Extract user_id (sub) from the JWT in the Authorization header.
    
    NOTE: This implementation decodes the token WITHOUT verifying the signature.
    In a production environment, this should verify the signature using the Supabase JWT secret.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    try:
        # Expect "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        token = parts[1]
        
        # JWT is header.payload.signature
        token_parts = token.split('.')
        if len(token_parts) != 3:
            return None
            
        # Decode payload (2nd part)
        payload_b64 = token_parts[1]
        
        # Add padding if needed
        payload_b64 += '=' * (-len(payload_b64) % 4)
        
        payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
        
        return payload.get('sub')
        
    except Exception as e:
        current_app.logger.error(f"Error decoding JWT: {e}")
        return None
