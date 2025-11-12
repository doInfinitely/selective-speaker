"""
Audio playback routes for streaming utterance audio segments.
"""

from fastapi import APIRouter, HTTPException, Response, Depends
from sqlalchemy.orm import Session
from typing import Annotated
from loguru import logger
from app.db import session_scope
from app import models
from app.storage import local_path
from app.utils.audio_extraction import extract_audio_segment
from app.dependencies import get_current_user_uid

router = APIRouter(prefix="/audio", tags=["audio"])


@router.get("/utterances/{utterance_id}")
async def get_utterance_audio(
    utterance_id: int,
    user_uid: Annotated[str, Depends(get_current_user_uid)] = None
):
    """
    Get audio for a specific utterance.
    
    Returns the audio segment as WAV file for playback in frontend.
    
    Args:
        utterance_id: ID of the utterance
    
    Returns:
        Audio segment as WAV file
    """
    with session_scope() as db:  # type: Session
        # Get user
        user = db.query(models.User).filter_by(uid=user_uid).first()
        if not user:
            raise HTTPException(status_code=403, detail="User not found")
        
        # Get utterance (stored as Segment) and chunk
        utterance = db.query(models.Segment).filter_by(id=utterance_id).first()
        
        if not utterance:
            raise HTTPException(status_code=404, detail=f"Utterance {utterance_id} not found")
        
        chunk = db.query(models.Chunk).filter_by(id=utterance.chunk_id).first()
        
        if not chunk:
            raise HTTPException(
                status_code=404,
                detail=f"Chunk {utterance.chunk_id} not found for utterance {utterance_id}"
            )
        
        # Authorization check: verify user owns this chunk
        if chunk.user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this audio"
            )
        
        # Get data before session closes
        chunk_audio_url = chunk.audio_url
        start_ms = utterance.start_ms
        end_ms = utterance.end_ms
        utterance_text = utterance.text
    
    # Get audio file path
    audio_path = local_path(chunk_audio_url)
    
    if not audio_path.exists():
        logger.error(f"Audio file not found: {audio_path}")
        raise HTTPException(
            status_code=404,
            detail=f"Audio file not found: {chunk_audio_url}"
        )
    
    try:
        # Extract audio segment
        audio_bytes = extract_audio_segment(
            input_path=audio_path,
            start_ms=start_ms,
            end_ms=end_ms
        )
        
        logger.info(
            f"Serving audio for utterance {utterance_id}: "
            f"{len(audio_bytes)} bytes, {end_ms - start_ms}ms"
        )
        
        # Return as WAV file
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f'inline; filename="utterance_{utterance_id}.wav"',
                "Content-Length": str(len(audio_bytes)),
                "Accept-Ranges": "bytes"
            }
        )
        
    except Exception as e:
        logger.error(f"Error extracting audio for utterance {utterance_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract audio: {e}"
        )


@router.get("/chunks/{chunk_id}")
async def get_chunk_audio(
    chunk_id: int,
    user_uid: Annotated[str, Depends(get_current_user_uid)] = None
):
    """
    Get full audio for a chunk.
    
    Returns the entire chunk audio file.
    
    Args:
        chunk_id: ID of the chunk
    
    Returns:
        Full chunk audio as WAV file
    """
    with session_scope() as db:  # type: Session
        # Get user
        user = db.query(models.User).filter_by(uid=user_uid).first()
        if not user:
            raise HTTPException(status_code=403, detail="User not found")
        
        chunk = db.query(models.Chunk).filter_by(id=chunk_id).first()
        
        if not chunk:
            raise HTTPException(status_code=404, detail=f"Chunk {chunk_id} not found")
        
        # Authorization check
        if chunk.user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this audio"
            )
        
        chunk_audio_url = chunk.audio_url
    
    # Get audio file path
    audio_path = local_path(chunk_audio_url)
    
    if not audio_path.exists():
        logger.error(f"Audio file not found: {audio_path}")
        raise HTTPException(
            status_code=404,
            detail=f"Audio file not found: {chunk_audio_url}"
        )
    
    try:
        # Read full file
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
        
        logger.info(f"Serving chunk {chunk_id} audio: {len(audio_bytes)} bytes")
        
        # Return as WAV file
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f'inline; filename="chunk_{chunk_id}.wav"',
                "Content-Length": str(len(audio_bytes)),
                "Accept-Ranges": "bytes"
            }
        )
        
    except Exception as e:
        logger.error(f"Error reading chunk audio {chunk_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read audio: {e}"
        )

