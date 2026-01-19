"""Firebase Admin SDK initialization."""
import firebase_admin
from firebase_admin import credentials
import os
import json
import logging

logger = logging.getLogger(__name__)

_firebase_initialized = False


def initialize_firebase():
    """
    Initialize Firebase Admin SDK with service account credentials.
    This should be called once when the application starts.
    
    Credentials are loaded in this order:
    1. FIREBASE_SERVICE_ACCOUNT_JSON env var (JSON string)
    2. FIREBASE_ADMIN_SDK_PATH env var (path to JSON file)
    3. Default file locations
    """
    global _firebase_initialized
    
    if _firebase_initialized or firebase_admin._apps:
        logger.debug("Firebase Admin SDK already initialized")
        return True
    
    cred = None
    
    # Option 1: Try JSON from environment variable (for Render/production)
    json_env = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    if json_env:
        try:
            service_account_info = json.loads(json_env)
            cred = credentials.Certificate(service_account_info)
            logger.info("Firebase credentials loaded from FIREBASE_SERVICE_ACCOUNT_JSON env var")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
        except Exception as e:
            logger.error(f"Error loading credentials from env var: {e}")
    
    # Option 2: Try file path from environment variable
    if not cred:
        cred_path = os.getenv('FIREBASE_ADMIN_SDK_PATH')
        
        if not cred_path:
            # Default locations to check
            possible_paths = [
                'attuned-firebase-adminsdk.json',
                os.path.join(os.path.dirname(__file__), '..', 'attuned-firebase-adminsdk.json'),
                os.path.join(os.path.dirname(__file__), '..', '..', 'attuned-firebase-adminsdk.json'),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    cred_path = path
                    break
        
        if cred_path and os.path.exists(cred_path):
            try:
                cred = credentials.Certificate(cred_path)
                logger.info(f"Firebase credentials loaded from file: {cred_path}")
            except Exception as e:
                logger.error(f"Error loading credentials from file: {e}")
    
    if not cred:
        logger.warning(
            "Firebase credentials not found. Push notifications will not work. "
            "Set FIREBASE_SERVICE_ACCOUNT_JSON (JSON string) or FIREBASE_ADMIN_SDK_PATH (file path)."
        )
        return False
    
    try:
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("✅ Firebase Admin SDK initialized")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return False


def is_firebase_initialized():
    """Check if Firebase is initialized."""
    return _firebase_initialized or bool(firebase_admin._apps)
