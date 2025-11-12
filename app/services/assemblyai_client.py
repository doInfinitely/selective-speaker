"""
AssemblyAI client for speech-to-text with diarization.

Documentation: https://www.assemblyai.com/docs
"""

import hmac
import hashlib
import httpx
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger
from app.config import settings


# AssemblyAI API endpoints
ASSEMBLYAI_API_BASE = "https://api.assemblyai.com/v2"
UPLOAD_ENDPOINT = f"{ASSEMBLYAI_API_BASE}/upload"
TRANSCRIPT_ENDPOINT = f"{ASSEMBLYAI_API_BASE}/transcript"


def verify_signature(headers: Dict[str, str], body: bytes, secret: str) -> bool:
    """
    Verify AssemblyAI webhook signature.
    
    AssemblyAI signs webhooks using HMAC-SHA256. The signature is in the
    "x-assemblyai-signature" header.
    
    Args:
        headers: Request headers dict
        body: Raw request body bytes
        secret: Webhook secret for HMAC verification
    
    Returns:
        True if signature is valid, False otherwise
    """
    signature = headers.get("x-assemblyai-signature", "")
    if not signature:
        logger.warning("No signature found in webhook headers")
        return False
    
    # Compute expected signature
    expected = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(signature, expected)
    
    if not is_valid:
        logger.warning("Webhook signature verification failed")
    
    return is_valid


async def upload_audio_file(file_path: Path) -> str:
    """
    Upload audio file to AssemblyAI.
    
    Args:
        file_path: Path to audio file
    
    Returns:
        Upload URL that can be used for transcription
    
    Raises:
        httpx.HTTPError: If upload fails
        ValueError: If API key is not configured
    """
    if not settings.ASSEMBLYAI_API_KEY:
        raise ValueError("ASSEMBLYAI_API_KEY not configured")
    
    logger.info(f"Uploading audio file: {file_path}")
    
    headers = {
        "authorization": settings.ASSEMBLYAI_API_KEY
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        with open(file_path, 'rb') as f:
            response = await client.post(
                UPLOAD_ENDPOINT,
                headers=headers,
                content=f.read()
            )
            response.raise_for_status()
            data = response.json()
            upload_url = data.get("upload_url")
            
            if not upload_url:
                raise ValueError("No upload_url in response")
            
            logger.info(f"Audio uploaded successfully: {upload_url}")
            return upload_url


async def submit_transcription(
    audio_url: str,
    user_id: int,
    chunk_id: int,
    enrollment_ms: int,
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit audio for transcription with diarization to AssemblyAI.
    
    Args:
        audio_url: URL to audio file (from upload_audio_file or external URL)
        user_id: User ID for metadata
        chunk_id: Chunk ID for metadata
        enrollment_ms: Enrollment duration in ms for metadata
        webhook_url: Optional webhook URL for completion callback
    
    Returns:
        Response dict with transcript ID and status:
        {
            "id": "transcript_id",
            "status": "queued",
            "audio_url": "...",
            ...
        }
    
    Raises:
        httpx.HTTPError: If submission fails
        ValueError: If API key is not configured
    """
    if not settings.ASSEMBLYAI_API_KEY:
        raise ValueError("ASSEMBLYAI_API_KEY not configured")
    
    # Build webhook URL if not provided
    if webhook_url is None:
        webhook_url = f"{settings.WEBHOOK_BASE_URL}/webhooks/assemblyai"
    
    logger.info(f"Submitting transcription for chunk {chunk_id}, user {user_id}")
    
    headers = {
        "authorization": settings.ASSEMBLYAI_API_KEY,
        "content-type": "application/json"
    }
    
    # Build payload - metadata must be stored separately and retrieved later
    # AssemblyAI doesn't support custom_metadata in the way we need, so we'll
    # need to track transcription_id -> metadata mapping in our database
    payload = {
        "audio_url": audio_url,
        # Enable speaker diarization
        "speaker_labels": True,
        # Request word-level timestamps and speaker info
        "format_text": False,
    }
    
    # Add webhook URL if provided
    if webhook_url:
        payload["webhook_url"] = webhook_url
    
    logger.info(f"Payload: {payload}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            TRANSCRIPT_ENDPOINT,
            headers=headers,
            json=payload
        )
        
        # Log response for debugging
        if response.status_code != 200:
            logger.error(
                f"AssemblyAI API error {response.status_code}: {response.text}"
            )
        
        response.raise_for_status()
        data = response.json()
        
        logger.info(
            f"Transcription submitted: {data.get('id')}, status: {data.get('status')}"
        )
        
        return data


async def get_transcription(transcript_id: str) -> Dict[str, Any]:
    """
    Poll for transcription results.
    
    This is useful if you want to poll instead of using webhooks.
    
    Args:
        transcript_id: Transcript ID from submit_transcription
    
    Returns:
        Transcription result including status, text, words with speaker labels
    
    Raises:
        httpx.HTTPError: If request fails
        ValueError: If API key is not configured
    """
    if not settings.ASSEMBLYAI_API_KEY:
        raise ValueError("ASSEMBLYAI_API_KEY not configured")
    
    headers = {
        "authorization": settings.ASSEMBLYAI_API_KEY
    }
    
    url = f"{TRANSCRIPT_ENDPOINT}/{transcript_id}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


def extract_diarized_words(transcript_data: Dict[str, Any]) -> list:
    """
    Extract word-level diarization from AssemblyAI transcript.
    
    Args:
        transcript_data: Full transcript response from AssemblyAI
    
    Returns:
        List of words with speaker labels in format expected by diarization_mapper:
        [
            {"start": int_ms, "end": int_ms, "speaker": "A", "confidence": float, "text": str},
            ...
        ]
    """
    words = transcript_data.get("words", [])
    
    # Transform AssemblyAI format to our internal format
    result = []
    for word in words:
        result.append({
            "start": word.get("start", 0),
            "end": word.get("end", 0),
            "speaker": word.get("speaker", "UNKNOWN"),
            "confidence": word.get("confidence", 1.0),
            "text": word.get("text", "")
        })
    
    return result
