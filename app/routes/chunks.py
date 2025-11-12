from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from pathlib import Path
from loguru import logger
from typing import Optional, Annotated
from app.db import session_scope
from app import models, schemas
from app.storage import local_path, save_uploaded_file
from app.utils.audio import concatenate_audio_files, WAVInfo
from app.services.assemblyai_client import upload_audio_file, submit_transcription
from app.dependencies import get_current_user_uid, get_or_create_user

router = APIRouter(prefix="/chunks", tags=["chunks"])


async def process_chunk_transcription(
    user_id: int,
    chunk_id: int,
    chunk_audio_url: str
):
    """
    Background task to process chunk transcription.
    
    NEW APPROACH (no concatenation!):
    1. Upload chunk directly to AssemblyAI
    2. Submit transcription with diarization
    3. Webhook will use embeddings to match speakers
    """
    try:
        logger.info(f"Processing transcription for chunk {chunk_id}")
        
        # Get chunk file path
        chunk_path = local_path(chunk_audio_url)
        
        # Verify file exists
        if not chunk_path.exists():
            logger.error(f"Chunk file not found: {chunk_path}")
            return
        
        logger.info(f"Chunk audio: {chunk_path}")
        
        # Upload chunk directly to AssemblyAI (no concatenation!)
        logger.info(f"Uploading chunk to AssemblyAI")
        audio_url = await upload_audio_file(chunk_path)
        
        # Submit for transcription with diarization
        logger.info(f"Submitting transcription request")
        result = await submit_transcription(
            audio_url=audio_url,
            user_id=user_id,
            chunk_id=chunk_id,
            enrollment_ms=0  # Not used anymore
        )
        
        transcript_id = result.get('id')
        logger.info(
            f"Transcription submitted for chunk {chunk_id}: "
            f"transcript_id={transcript_id}, status={result.get('status')}"
        )
        
        # Store transcript_id in database for webhook lookup
        with session_scope() as db:
            chunk = db.query(models.Chunk).filter_by(id=chunk_id).first()
            if chunk:
                chunk.transcript_id = transcript_id
                logger.info(f"Stored transcript_id {transcript_id} for chunk {chunk_id}")
        
    except Exception as e:
        logger.error(f"Error processing chunk {chunk_id}: {e}", exc_info=True)


@router.post("/upload")
async def upload_chunk(
    file: UploadFile = File(...),
    device_id: Optional[str] = Form(None),
    gps_lat: Optional[str] = Form(None),
    gps_lon: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user_uid: Annotated[str, Depends(get_current_user_uid)] = None
):
    """
    Upload audio chunk file from mobile app.
    
    This endpoint receives the actual audio file and processes it.
    """
    try:
        # Save uploaded file
        filename = f"chunk_{file.filename}"
        file_path = save_uploaded_file(file, filename)
        logger.info(f"Saved uploaded chunk: {filename}")
        
        # Convert form data
        lat = float(gps_lat) if gps_lat else None
        lon = float(gps_lon) if gps_lon else None
        
        # Create chunk request
        chunk_data = schemas.ChunkSubmit(
            audio_url=filename,
            device_id=device_id,
            gps_lat=lat,
            gps_lon=lon
        )
        
        # Process like normal submit (pass user_uid)
        return await submit_chunk(chunk_data, background_tasks, user_uid)
        
    except Exception as e:
        logger.error(f"Error uploading chunk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/submit")
async def submit_chunk(
    payload: schemas.ChunkSubmit, 
    background_tasks: BackgroundTasks,
    user_uid: Annotated[str, Depends(get_current_user_uid)] = None
):
    """
    Submit a recorded audio chunk for transcription.
    
    Flow:
    1. Store chunk metadata in database
    2. Background task uploads chunk to AssemblyAI
    3. Submit for transcription with diarization
    4. AssemblyAI calls webhook when complete with results
    
    Args:
        payload: Chunk data including audio URL, timestamps, and GPS coordinates
        background_tasks: FastAPI background tasks
    
    Returns:
        Chunk ID and queued status
    """
    with session_scope() as db:
        # Get current user from auth token
        user = db.query(models.User).filter_by(uid=user_uid).first()
        if not user:
            # Create user if doesn't exist
            get_or_create_user(user_uid)
            user = db.query(models.User).filter_by(uid=user_uid).first()
        
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
        
        chunk_id = chunk.id
        enrollment_ms = enrollment.duration_ms
        
        # Queue transcription processing in background
        background_tasks.add_task(
            process_chunk_transcription,
            user_id=user.id,
            chunk_id=chunk_id,
            chunk_audio_url=payload.audio_url
        )
        
        logger.info(f"Chunk {chunk_id} submitted for transcription")
        
        return {
            "status": "queued",
            "chunk_id": chunk_id,
            "enrollment_id": enrollment.id,
            "enrollment_ms": enrollment_ms,
            "message": "Chunk queued for transcription"
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

