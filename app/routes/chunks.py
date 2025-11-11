from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.db import session_scope
from app import models, schemas

router = APIRouter(prefix="/chunks", tags=["chunks"])


@router.post("/submit")
def submit_chunk(payload: schemas.ChunkSubmit):
    """
    Submit a recorded audio chunk for transcription.
    
    Flow:
    1. Store chunk metadata in database
    2. Queue job to concatenate [enrollment audio] + [silence] + [chunk audio]
    3. Submit to AssemblyAI with diarization enabled
    4. Include metadata (user_id, chunk_id, enrollment_ms) for webhook processing
    
    Args:
        payload: Chunk data including audio URL, timestamps, and GPS coordinates
    
    Returns:
        Chunk ID and queued status
    """
    with session_scope() as db:
        # Get current user
        user = db.query(models.User).filter_by(uid="dev-uid").first()
        if not user:
            raise HTTPException(
                status_code=400,
                detail="User not found. Please complete enrollment first."
            )
        
        # Verify user has enrollment
        enrollment = db.query(models.Enrollment).filter_by(user_id=user.id).order_by(
            models.Enrollment.created_at.desc()
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=400,
                detail="No enrollment found. Please complete enrollment first."
            )
        
        # Create chunk record
        chunk = models.Chunk(
            user_id=user.id,
            audio_url=payload.audio_url,
            device_id=payload.device_id,
            start_ts=payload.start_ts,
            end_ts=payload.end_ts,
            gps_lat=payload.gps_lat,
            gps_lon=payload.gps_lon,
        )
        db.add(chunk)
        db.flush()
        
        # TODO: In production, enqueue STT job here
        # Job should:
        # 1. Concatenate enrollment audio + silence pad + chunk audio
        # 2. Upload to AssemblyAI with metadata:
        #    {user_id, chunk_id, enrollment_ms}
        # 3. Register webhook URL for completion callback
        
        # TODO: If GPS coordinates provided, queue geocoding job
        if payload.gps_lat is not None and payload.gps_lon is not None:
            # Queue geocoding job
            pass
        
        return {
            "status": "queued",
            "chunk_id": chunk.id,
            "enrollment_id": enrollment.id,
            "enrollment_ms": enrollment.duration_ms
        }


@router.get("/{chunk_id}")
def get_chunk(chunk_id: int):
    """
    Get chunk details and associated segments.
    
    Args:
        chunk_id: Chunk ID
    
    Returns:
        Chunk metadata and segments
    """
    with session_scope() as db:
        chunk = db.query(models.Chunk).filter_by(id=chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        segments = db.query(models.Segment).filter_by(chunk_id=chunk_id, kept=True).all()
        location = db.query(models.Location).filter_by(chunk_id=chunk_id).first()
        
        return {
            "chunk_id": chunk.id,
            "device_id": chunk.device_id,
            "start_ts": chunk.start_ts.isoformat() if chunk.start_ts else None,
            "end_ts": chunk.end_ts.isoformat() if chunk.end_ts else None,
            "gps_lat": chunk.gps_lat,
            "gps_lon": chunk.gps_lon,
            "address": location.address if location else None,
            "segments": [
                {
                    "id": seg.id,
                    "start_ms": seg.start_ms,
                    "end_ms": seg.end_ms,
                    "text": seg.text,
                    "confidence": seg.confidence
                }
                for seg in segments
            ]
        }

