"""
AssemblyAI client placeholder.

In production, this module would handle:
- Uploading audio to AssemblyAI
- Submitting transcription requests with diarization enabled
- Polling for results or handling webhooks
- Signature verification for webhook security

Expected webhook payload minimal shape:
{
  "id": "transcript_id",
  "metadata": {"user_id": 1, "chunk_id": 42, "enrollment_ms": 29000},
  "words": [
      {"start": 0, "end": 500, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "Hello"},
      ...
  ]
}
"""

from typing import Any, Dict
import hmac
import hashlib


def verify_signature(headers: Dict[str, str], body: bytes, secret: str) -> bool:
    """
    Verify AssemblyAI webhook signature.
    
    In production, implement HMAC verification using the signature from headers.
    For dev skeleton, always return True.
    
    Args:
        headers: Request headers dict
        body: Raw request body bytes
        secret: Webhook secret for HMAC verification
    
    Returns:
        True if signature is valid, False otherwise
    """
    # TODO: Implement real HMAC verification
    # signature = headers.get("x-assemblyai-signature", "")
    # expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    # return hmac.compare_digest(signature, expected)
    return True


async def submit_transcription(
    audio_url: str,
    user_id: int,
    chunk_id: int,
    enrollment_ms: int,
    webhook_url: str
) -> Dict[str, Any]:
    """
    Submit audio for transcription with diarization to AssemblyAI.
    
    In production:
    1. Upload concatenated audio ([enrollment] + [silence] + [chunk]) to AssemblyAI
    2. Submit transcription request with:
       - speaker_labels=True (diarization)
       - webhook_url for callback
       - metadata containing user_id, chunk_id, enrollment_ms
    
    Args:
        audio_url: URL or path to concatenated audio file
        user_id: User ID for metadata
        chunk_id: Chunk ID for metadata
        enrollment_ms: Enrollment duration for metadata
        webhook_url: URL for transcription completion webhook
    
    Returns:
        Response dict with transcript ID and status
    """
    # TODO: Implement actual AssemblyAI API call
    # import httpx
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(
    #         "https://api.assemblyai.com/v2/transcript",
    #         headers={"authorization": ASSEMBLYAI_API_KEY},
    #         json={
    #             "audio_url": audio_url,
    #             "speaker_labels": True,
    #             "webhook_url": webhook_url,
    #             "metadata": {
    #                 "user_id": user_id,
    #                 "chunk_id": chunk_id,
    #                 "enrollment_ms": enrollment_ms
    #             }
    #         }
    #     )
    #     return response.json()
    
    return {
        "id": "mock_transcript_id",
        "status": "queued"
    }

