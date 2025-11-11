from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class EnrollmentCreate(BaseModel):
    audio_url: str
    duration_ms: int
    phrase_text: Optional[str] = None
    edit_distance: Optional[int] = None


class ChunkSubmit(BaseModel):
    audio_url: str
    device_id: Optional[str] = None
    start_ts: Optional[datetime] = None
    end_ts: Optional[datetime] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None


class SegmentOut(BaseModel):
    id: int
    chunk_id: int
    start_ms: int
    end_ms: int
    text: str
    confidence: Optional[float]

    class Config:
        from_attributes = True


class UtteranceBubble(BaseModel):
    chunk_id: int
    start_ms: int
    end_ms: int
    text: str
    device_id: Optional[str]
    timestamp: Optional[datetime]
    address: Optional[str]

