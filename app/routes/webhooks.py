from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
from app.db import session_scope
from app import models
from app.config import settings
from app.services.diarization_mapper import map_enrollment_anchored
from app.services.assemblyai_client import verify_signature
from app.services.geocoding import reverse_geocode

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/assemblyai")
async def assemblyai_webhook(request: Request):
    """
    Handle AssemblyAI transcription completion webhook.
    
    Process flow:
    1. Verify webhook signature for security
    2. Extract transcribed words with speaker labels
    3. Use enrollment-anchored mapping to identify user's speech
    4. Store only segments that match the enrolled speaker
    5. Optionally trigger geocoding if GPS coordinates present
    
    Expected payload structure:
    {
        "id": "transcript_id",
        "status": "completed",
        "metadata": {
            "user_id": 123,
            "chunk_id": 456,
            "enrollment_ms": 30000
        },
        "words": [
            {"start": 0, "end": 500, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "Hello"},
            ...
        ]
    }
    """
    body = await request.body()
    
    # Verify webhook signature
    if not verify_signature(dict(request.headers), body, settings.ASSEMBLYAI_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    
    # Extract metadata
    words = payload.get("words", [])
    metadata = payload.get("metadata", {})
    user_id = metadata.get("user_id")
    chunk_id = metadata.get("chunk_id")
    enrollment_ms = metadata.get("enrollment_ms")

    if not (user_id and chunk_id and enrollment_ms is not None):
        raise HTTPException(status_code=400, detail="Missing required metadata")

    # Map enrollment-anchored diarization to find user segments
    result = map_enrollment_anchored(words, enroll_ms=int(enrollment_ms))
    
    if result.get("status") != "ok":
        # Diarization failed or no user speech detected
        return {
            "status": "ignored",
            "reason": result.get("reason", "indeterminate"),
            "chunk_id": chunk_id
        }

    kept_segments = result["kept"]
    user_label = result.get("user_label", "USER")

    # Persist segments to database
    with session_scope() as db:
        # Verify chunk exists
        chunk = db.query(models.Chunk).filter_by(id=chunk_id).first()
        if not chunk:
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
        
        # Trigger geocoding if GPS coordinates present
        if chunk.gps_lat is not None and chunk.gps_lon is not None:
            # Check if location already exists
            existing_location = db.query(models.Location).filter_by(chunk_id=chunk_id).first()
            if not existing_location:
                address = await reverse_geocode(chunk.gps_lat, chunk.gps_lon)
                if address:
                    location = models.Location(
                        chunk_id=chunk_id,
                        address=address,
                        source="geocoder"
                    )
                    db.add(location)
    
    return {
        "status": "ok",
        "chunk_id": chunk_id,
        "kept_count": len(kept_segments),
        "user_label": user_label
    }

