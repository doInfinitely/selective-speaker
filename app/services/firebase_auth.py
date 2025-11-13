"""
Firebase Authentication service for verifying ID tokens.
"""

import firebase_admin
from firebase_admin import credentials, auth
from loguru import logger
from pathlib import Path
from typing import Optional
import os
import json


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
    
    # Check for JSON string first (Railway/production), then file path (local dev)
    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
    
    try:
        if service_account_json:
            # Load from JSON string (Railway/production)
            cred_dict = json.loads(service_account_json)
            cred = credentials.Certificate(cred_dict)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized from JSON environment variable")
            return _firebase_app
        elif service_account_path:
            # Load from file path (local development)
            service_account_file = Path(service_account_path)
            if not service_account_file.exists():
                logger.error(f"Firebase service account file not found: {service_account_path}")
                return None
            cred = credentials.Certificate(str(service_account_file))
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized from file path")
            return _firebase_app
        else:
            logger.warning("Neither FIREBASE_SERVICE_ACCOUNT_JSON nor FIREBASE_SERVICE_ACCOUNT_KEY set - Firebase auth disabled")
            return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
        return None
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

