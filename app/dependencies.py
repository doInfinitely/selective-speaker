"""
FastAPI dependencies for authentication and authorization.
"""

from fastapi import Header, HTTPException, Depends
from typing import Optional, Annotated
from loguru import logger
from app.services.firebase_auth import verify_id_token
from app.db import session_scope
from app import models
from sqlalchemy.orm import Session


async def get_current_user_uid(
    authorization: Annotated[Optional[str], Header()] = None
) -> str:
    """
    Extract and verify Firebase ID token from Authorization header.
    
    Args:
        authorization: Authorization header value ("Bearer <token>")
    
    Returns:
        User UID from verified token
    
    Raises:
        HTTPException: If token is missing or invalid
    """
    # Development mode: allow requests without auth
    # TODO: Remove this in production!
    if not authorization:
        logger.warning("⚠️ No authorization header - using dev-uid for development")
        return "dev-uid"
    
    # Extract token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: Bearer <token>"
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # Verify token
    decoded_token = verify_id_token(token)
    
    if not decoded_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token"
        )
    
    uid = decoded_token.get('uid')
    
    if not uid:
        raise HTTPException(
            status_code=401,
            detail="Token missing user ID"
        )
    
    logger.debug(f"Authenticated user: {uid}")
    return uid


def get_or_create_user(uid: str, email: Optional[str] = None, display_name: Optional[str] = None) -> models.User:
    """
    Get or create a user from Firebase UID.
    
    Args:
        uid: Firebase user ID
        email: User email (optional)
        display_name: User display name (optional)
    
    Returns:
        User model instance
    """
    with session_scope() as db:
        user = db.query(models.User).filter_by(uid=uid).first()
        
        if not user:
            user = models.User(
                uid=uid,
                email=email or f"{uid}@placeholder.com",
                display_name=display_name or "User"
            )
            db.add(user)
            db.flush()
            logger.info(f"Created new user: {uid}")
        
        return user

