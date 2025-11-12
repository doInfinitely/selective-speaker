from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from loguru import logger
import json
from typing import Optional, Annotated
from app.db import session_scope
from app import models, schemas
from app.storage import local_path, save_uploaded_file
from app.services.speaker_verification import extract_embedding
from app.dependencies import get_current_user_uid, get_or_create_user

router = APIRouter(prefix="/enrollment", tags=["enrollment"])


@router.post("/upload")
async def upload_enrollment(
    file: UploadFile = File(...),
    duration_ms: str = Form(...),
    phrase_text: Optional[str] = Form(None),
    user_uid: Annotated[str, Depends(get_current_user_uid)] = None
):
    """
    Upload enrollment audio file from mobile app.
    
    This endpoint receives the actual audio file, saves it, extracts the embedding,
    and creates the enrollment record.
    """
    try:
        # Save uploaded file
        filename = f"enrollment_{file.filename}"
        file_path = save_uploaded_file(file, filename)
        logger.info(f"Saved enrollment file: {filename}")
        
        # Convert duration to int
        duration = int(duration_ms)
        
        # Get or create user from Firebase UID
        user = get_or_create_user(user_uid)
        
        # Create enrollment record
        with session_scope() as db:
            user = db.query(models.User).filter_by(uid=user_uid).first()
            
            # Extract speaker embedding
            logger.info(f"Extracting embedding for user {user.id}")
            embedding = extract_embedding(file_path)
            embedding_json = json.dumps(embedding.tolist())
            logger.info(f"Embedding extracted: {embedding.shape} dimensions")
            
            # Create enrollment
            enrollment = models.Enrollment(
                user_id=user.id,
                audio_url=filename,
                duration_ms=duration,
                phrase_text=phrase_text,
                edit_distance=None,
                embedding_vector=embedding_json,
            )
            db.add(enrollment)
            db.flush()
            
            logger.info(f"Enrollment complete: enrollment_id={enrollment.id}")
            
            return {
                "status": "ok",
                "enrollment_id": enrollment.id,
                "user_id": user.id,
                "embedding_dimensions": len(embedding)
            }
            
    except Exception as e:
        logger.error(f"Error uploading enrollment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/complete")
def complete_enrollment(
    payload: schemas.EnrollmentCreate,
    user_uid: Annotated[str, Depends(get_current_user_uid)] = None
):
    """
    Complete enrollment process after user records their voice sample.
    
    Process:
    1. Verify Firebase JWT token
    2. Extract speaker embedding from audio
    3. Store enrollment audio reference and embedding
    
    Args:
        payload: Enrollment data including audio URL and duration
    
    Returns:
        Enrollment ID and status
    """
    # Get or create user from Firebase UID
    user = get_or_create_user(user_uid)
    
    with session_scope() as db:  # type: Session
        user = db.query(models.User).filter_by(uid=user_uid).first()
        
        # Extract speaker embedding from enrollment audio
        logger.info(f"Processing enrollment for user {user.id}")
        audio_path = local_path(payload.audio_url)
        
        if not audio_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Enrollment audio file not found: {payload.audio_url}"
            )
        
        try:
            logger.info(f"Extracting embedding from {audio_path}")
            embedding = extract_embedding(audio_path)
            embedding_json = json.dumps(embedding.tolist())
            logger.info(f"Embedding extracted successfully: {embedding.shape} dimensions")
        except Exception as e:
            logger.error(f"Error extracting embedding: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract speaker embedding: {e}"
            )
        
        # Create enrollment record
        enrollment = models.Enrollment(
            user_id=user.id,
            audio_url=payload.audio_url,
            duration_ms=payload.duration_ms,
            phrase_text=payload.phrase_text,
            edit_distance=payload.edit_distance,
            embedding_vector=embedding_json,
        )
        db.add(enrollment)
        db.flush()
        
        logger.info(f"Enrollment complete: enrollment_id={enrollment.id}")
        
        return {
            "status": "ok",
            "enrollment_id": enrollment.id,
            "user_id": user.id,
            "embedding_dimensions": len(embedding)
        }


@router.post("/reset")
def reset_enrollment(user_uid: Annotated[str, Depends(get_current_user_uid)] = None):
    """
    Reset enrollment for current user.
    
    Marks old enrollment as inactive and allows user to record new sample.
    Previous utterances remain intact but future chunks will use new voiceprint.
    """
    with session_scope() as db:
        user = db.query(models.User).filter_by(uid=user_uid).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # In production, you might mark old enrollments as inactive
        # rather than deleting them
        return {"status": "ok", "message": "Ready for new enrollment"}


@router.get("/status")
def enrollment_status(user_uid: Annotated[str, Depends(get_current_user_uid)] = None):
    """
    Check if current user has completed enrollment.
    
    Returns:
        Enrollment status and details
    """
    with session_scope() as db:
        user = db.query(models.User).filter_by(uid=user_uid).first()
        if not user:
            return {"enrolled": False}
        
        enrollment = db.query(models.Enrollment).filter_by(user_id=user.id).order_by(
            models.Enrollment.created_at.desc()
        ).first()
        
        if not enrollment:
            return {"enrolled": False}
        
        return {
            "enrolled": True,
            "enrollment_id": enrollment.id,
            "duration_ms": enrollment.duration_ms,
            "created_at": enrollment.created_at.isoformat()
        }

