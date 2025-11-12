"""
Firebase Authentication service for verifying ID tokens.
"""

import firebase_admin
from firebase_admin import credentials, auth
from loguru import logger
from pathlib import Path
from typing import Optional
import os


_firebase_app = None


def initialize_firebase():
    """
    Initialize Firebase Admin SDK.
    
    Requires FIREBASE_SERVICE_ACCOUNT_KEY environment variable pointing to
    the service account JSON file path.
    """
    global _firebase_app
    
    if _firebase_app is not None:
        return _firebase_app
    
    # Check if already initialized
    try:
        _firebase_app = firebase_admin.get_app()
        logger.info("Firebase already initialized")
        return _firebase_app
    except ValueError:
        pass
    
    # Get service account key path from environment
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
    
    if not service_account_path:
        logger.warning("FIREBASE_SERVICE_ACCOUNT_KEY not set - Firebase auth disabled for development")
        return None
    
    service_account_file = Path(service_account_path)
    
    if not service_account_file.exists():
        logger.error(f"Firebase service account file not found: {service_account_path}")
        return None
    
    try:
        cred = credentials.Certificate(str(service_account_file))
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized successfully")
        return _firebase_app
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return None


def verify_id_token(id_token: str) -> Optional[dict]:
    """
    Verify a Firebase ID token and return the decoded token.
    
    Args:
        id_token: Firebase ID token from client
    
    Returns:
        Decoded token with user info (uid, email, etc.) or None if invalid
    """
    if not _firebase_app:
        initialize_firebase()
    
    if not _firebase_app:
        # Firebase not initialized (development mode)
        logger.warning("Firebase not initialized - skipping token verification")
        return None
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        logger.debug(f"Token verified for user: {decoded_token.get('uid')}")
        return decoded_token
    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid ID token: {e}")
        return None
    except auth.ExpiredIdTokenError as e:
        logger.warning(f"Expired ID token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying ID token: {e}")
        return None


# Initialize on module import
initialize_firebase()

