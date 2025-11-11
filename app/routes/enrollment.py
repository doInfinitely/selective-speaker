from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.db import session_scope
from app import models, schemas

router = APIRouter(prefix="/enrollment", tags=["enrollment"])


@router.post("/complete")
def complete_enrollment(payload: schemas.EnrollmentCreate):
    """
    Complete enrollment process after user records their voice sample.
    
    In production, this would:
    1. Verify Firebase JWT token
    2. Store enrollment audio reference
    3. Optionally verify the transcription matches expected phrase using Levenshtein distance
    4. Compute and store speaker embedding (if using embedding-based verification)
    
    Args:
        payload: Enrollment data including audio URL and duration
    
    Returns:
        Enrollment ID and status
    """
    with session_scope() as db:  # type: Session
        # TODO: In production, verify Firebase JWT and get real user
        # For now, use a dev user
        user = db.query(models.User).filter_by(uid="dev-uid").first()
        if not user:
            user = models.User(uid="dev-uid", display_name="Dev User", email="dev@example.com")
            db.add(user)
            db.flush()
        
        # Create enrollment record
        enrollment = models.Enrollment(
            user_id=user.id,
            audio_url=payload.audio_url,
            duration_ms=payload.duration_ms,
            phrase_text=payload.phrase_text,
            edit_distance=payload.edit_distance,
        )
        db.add(enrollment)
        db.flush()
        
        return {
            "status": "ok",
            "enrollment_id": enrollment.id,
            "user_id": user.id
        }


@router.post("/reset")
def reset_enrollment():
    """
    Reset enrollment for current user.
    
    Marks old enrollment as inactive and allows user to record new sample.
    Previous utterances remain intact but future chunks will use new voiceprint.
    """
    with session_scope() as db:
        user = db.query(models.User).filter_by(uid="dev-uid").first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # In production, you might mark old enrollments as inactive
        # rather than deleting them
        return {"status": "ok", "message": "Ready for new enrollment"}


@router.get("/status")
def enrollment_status():
    """
    Check if current user has completed enrollment.
    
    Returns:
        Enrollment status and details
    """
    with session_scope() as db:
        user = db.query(models.User).filter_by(uid="dev-uid").first()
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

