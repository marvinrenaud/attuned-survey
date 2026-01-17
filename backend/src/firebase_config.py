"""Firebase Admin SDK initialization."""
import firebase_admin
from firebase_admin import credentials
import os
import logging

logger = logging.getLogger(__name__)

_firebase_initialized = False


def initialize_firebase():
    """
    Initialize Firebase Admin SDK with service account credentials.
    This should be called once when the application starts.
    """
    global _firebase_initialized
    
    if _firebase_initialized or firebase_admin._apps:
        logger.debug("Firebase Admin SDK already initialized")
        return True
    
    # Path to Firebase service account JSON file
    # Check multiple locations
    cred_path = os.getenv('FIREBASE_ADMIN_SDK_PATH')
    
    if not cred_path:
        # Default locations to check
        possible_paths = [
            'attuned-firebase-adminsdk.json',  # Current directory
            os.path.join(os.path.dirname(__file__), '..', 'attuned-firebase-adminsdk.json'),  # backend/
            os.path.join(os.path.dirname(__file__), '..', '..', 'attuned-firebase-adminsdk.json'),  # project root
        ]
        for path in possible_paths:
            if os.path.exists(path):
                cred_path = path
                break
    
    if not cred_path or not os.path.exists(cred_path):
        logger.warning(
            "Firebase credentials not found. Push notifications will not work. "
            "Set FIREBASE_ADMIN_SDK_PATH environment variable or place credentials file in backend directory."
        )
        return False

    
    try:
        cred = credentials.Certificate(cred_path)
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
