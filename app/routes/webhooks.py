from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
from loguru import logger
import json
import numpy as np
from app.db import session_scope
from app import models
from app.config import settings
from app.services.assemblyai_client import verify_signature, extract_diarized_words, get_transcription
from app.services.geocoding import reverse_geocode
from app.services.speaker_verification import (
    extract_embeddings_per_speaker,
    match_speaker_to_enrollment
)
from app.storage import local_path

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/assemblyai")
async def assemblyai_webhook(request: Request):
    """
    Handle AssemblyAI transcription completion webhook.
    
    Process flow:
    1. Verify webhook signature for security
    2. Check transcription status
    3. Extract transcribed words with speaker labels
    4. Use enrollment-anchored mapping to identify user's speech
    5. Store only segments that match the enrolled speaker
    6. Optionally trigger geocoding if GPS coordinates present
    
    AssemblyAI webhook payload:
    {
        "transcript_id": "...",
        "status": "completed",
        "custom_metadata": {
            "user_id": "123",
            "chunk_id": "456",
            "enrollment_ms": "30000"
        },
        "text": "full transcript...",
        "words": [
            {"start": 0, "end": 500, "speaker": "A", "confidence": 0.9, "text": "Hello"},
            ...
        ],
        ...
    }
    """
    body = await request.body()
    
    # Verify webhook signature (if configured)
    if settings.ASSEMBLYAI_WEBHOOK_SECRET and settings.ASSEMBLYAI_WEBHOOK_SECRET != "devsecret":
        if not verify_signature(dict(request.headers), body, settings.ASSEMBLYAI_WEBHOOK_SECRET):
            logger.warning("Webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    payload = await request.json()
    
    transcript_id = payload.get("transcript_id") or payload.get("id")
    status = payload.get("status")
    
    logger.info(f"Received webhook for transcript {transcript_id}, status: {status}")
    
    # Check if transcription completed successfully
    if status != "completed":
        logger.warning(f"Transcript {transcript_id} not completed: {status}")
        return {
            "status": "ignored",
            "reason": f"transcript_status_{status}",
            "transcript_id": transcript_id
        }
    
    # Look up chunk by transcript_id
    with session_scope() as lookup_db:
        chunk = lookup_db.query(models.Chunk).filter_by(transcript_id=transcript_id).first()
        
        if not chunk:
            logger.error(f"No chunk found for transcript_id {transcript_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No chunk found for transcript_id {transcript_id}"
            )
        
        chunk_id = chunk.id
        user_id = chunk.user_id
        chunk_audio_url = chunk.audio_url
        
        # Check if this chunk has already been processed (idempotency check)
        existing_segments = lookup_db.query(models.Segment).filter_by(chunk_id=chunk_id).count()
        if existing_segments > 0:
            logger.warning(f"Chunk {chunk_id} already has {existing_segments} segments - skipping duplicate webhook")
            return {
                "status": "already_processed",
                "chunk_id": chunk_id,
                "existing_segments": existing_segments,
                "transcript_id": transcript_id
            }
        
        # Get enrollment to retrieve embedding
        user = lookup_db.query(models.User).filter_by(id=user_id).first()
        enrollment = lookup_db.query(models.Enrollment).filter_by(user_id=user_id).order_by(
            models.Enrollment.created_at.desc()
        ).first()
        
        if not enrollment:
            logger.error(f"No enrollment found for user {user_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No enrollment found for user {user_id}"
            )
        
        # Extract data from enrollment BEFORE session closes
        enrollment_id = enrollment.id
        enrollment_embedding_json = enrollment.embedding_vector
        
        if not enrollment_embedding_json:
            logger.error(f"No embedding vector in enrollment {enrollment_id}")
            raise HTTPException(
                status_code=500,
                detail="Enrollment missing embedding vector. Please re-enroll."
            )
        
    logger.info(f"Found chunk {chunk_id} for user {user_id}")
    
    # Parse enrollment embedding (outside session, but we have the JSON data)
    enrollment_embedding = np.array(json.loads(enrollment_embedding_json))
    logger.info(f"Loaded enrollment embedding: {enrollment_embedding.shape}")
    
    # Fetch the full transcript from AssemblyAI
    logger.info(f"Fetching full transcript for {transcript_id}")
    try:
        full_transcript = await get_transcription(transcript_id)
        logger.info(f"Fetched transcript: {len(full_transcript.get('words', []))} words")
    except Exception as e:
        logger.error(f"Error fetching transcript {transcript_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch transcript: {e}"
        )
    
    # Extract diarized words from the full transcript
    words = extract_diarized_words(full_transcript)
    
    if not words:
        logger.warning(f"No words in transcript {transcript_id}")
        return {
            "status": "ignored",
            "reason": "no_words",
            "chunk_id": chunk_id
        }
    
    logger.info(f"Processing {len(words)} words for chunk {chunk_id}")
    
    # Extract embeddings for each speaker in the chunk
    chunk_audio_path = local_path(chunk_audio_url)
    if not chunk_audio_path.exists():
        logger.error(f"Chunk audio not found: {chunk_audio_path}")
        raise HTTPException(status_code=404, detail="Chunk audio file not found")
    
    logger.info("Extracting embeddings per speaker...")
    speaker_embeddings = extract_embeddings_per_speaker(chunk_audio_path, words, min_duration_ms=1000)
    
    if not speaker_embeddings:
        logger.warning("No speakers found in chunk with sufficient duration")
        return {
            "status": "ignored",
            "reason": "no_valid_speakers",
            "chunk_id": chunk_id
        }
    
    # Match speakers to enrollment using embeddings
    matched_speaker = match_speaker_to_enrollment(
        enrollment_embedding,
        speaker_embeddings,
        threshold=0.25  # Lowered to capture short utterances and environmental variance
    )
    
    if not matched_speaker:
        logger.warning(f"No speaker matched enrollment for chunk {chunk_id}")
        return {
            "status": "ignored",
            "reason": "no_matching_speaker",
            "chunk_id": chunk_id
        }
    
    logger.info(f"Matched speaker: {matched_speaker}")
    
    # Filter words to keep only from matched speaker
    user_words = [w for w in words if w["speaker"] == matched_speaker]
    logger.info(f"Found {len(user_words)} words from matched speaker")
    
    # Group words into segments (merge close words)
    segments = []
    current_segment = []
    GAP_MS = settings.SEGMENT_GAP_MS
    
    for word in user_words:
        if not current_segment:
            current_segment = [word]
        elif word["start"] - current_segment[-1]["end"] <= GAP_MS:
            current_segment.append(word)
        else:
            segments.append(current_segment)
            current_segment = [word]
    
    if current_segment:
        segments.append(current_segment)
    
    # Filter segments by duration and length
    kept_segments = []
    for seg in segments:
        start_ms = seg[0]["start"]
        end_ms = seg[-1]["end"]
        duration = end_ms - start_ms
        text = " ".join(w["text"] for w in seg)
        
        if duration >= settings.SEGMENT_MIN_MS and len(text) >= settings.SEGMENT_MIN_CHARS:
            kept_segments.append({
                "start_ms": start_ms,
                "end_ms": end_ms,
                "text": text,
                "avg_conf": sum(w.get("confidence", 1.0) for w in seg) / len(seg)
            })
            logger.info(f"  ✓ Segment: {duration}ms, \"{text[:50]}...\"")
    
    user_label = matched_speaker
    
    logger.info(f"Found {len(kept_segments)} user segments for chunk {chunk_id}")
    
    # Persist segments to database
    with session_scope() as db:
        # Verify chunk exists
        chunk = db.query(models.Chunk).filter_by(id=chunk_id).first()
        if not chunk:
            logger.error(f"Chunk {chunk_id} not found in database")
            raise HTTPException(status_code=404, detail=f"Chunk {chunk_id} not found")
        
        # Store each kept segment
        for seg in kept_segments:
            segment = models.Segment(
                chunk_id=chunk_id,
                speaker_label=user_label,
                start_ms=seg["start_ms"],
                end_ms=seg["end_ms"],
                text=seg["text"],
                confidence=seg.get("avg_conf"),
                kept=True,
            )
            db.add(segment)
        
        logger.info(f"Stored {len(kept_segments)} segments for chunk {chunk_id}")
        
        # Trigger geocoding if GPS coordinates present
        if chunk.gps_lat is not None and chunk.gps_lon is not None:
            # Check if location already exists
            existing_location = db.query(models.Location).filter_by(chunk_id=chunk_id).first()
            if not existing_location:
                try:
                    address = await reverse_geocode(chunk.gps_lat, chunk.gps_lon)
                    if address:
                        location = models.Location(
                            chunk_id=chunk_id,
                            address=address,
                            source="geocoder"
                        )
                        db.add(location)
                        logger.info(f"Geocoded location for chunk {chunk_id}: {address}")
                except Exception as e:
                    logger.error(f"Geocoding failed for chunk {chunk_id}: {e}")
    
    return {
        "status": "ok",
        "chunk_id": chunk_id,
        "kept_count": len(kept_segments),
        "user_label": user_label,
        "transcript_id": transcript_id
    }

