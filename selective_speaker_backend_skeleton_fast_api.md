# Selective Speaker Backend Skeleton (FastAPI)

A production-ready skeleton for a diarization-only selective-speaker backend. Includes:

- FastAPI service with routes (`/enrollment`, `/chunks`, `/utterances`, webhooks)
- Postgres models (SQLAlchemy 2.0) & Pydantic schemas
- AssemblyAI webhook handler + diarization-only **enrollment-anchored** mapping
- Local file storage for dev; interface to swap in S3/GCS later
- Test harness & script to run the diarization mapper on `[enroll.wav, chunk.wav]` with a mocked STT JSON
- Docker Compose for Postgres

---

## File tree
```
selective-speaker-backend/
├─ pyproject.toml
├─ alembic.ini
├─ .env.example
├─ docker-compose.yml
├─ README.md
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ db.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ storage.py
│  ├─ services/
│  │  ├─ diarization_mapper.py
│  │  ├─ assemblyai_client.py
│  │  └─ geocoding.py
│  ├─ routes/
│  │  ├─ enrollment.py
│  │  ├─ chunks.py
│  │  ├─ utterances.py
│  │  └─ webhooks.py
│  └─ utils/
│     └─ audio.py
└─ tests/
   ├─ test_diarization_mapper.py
   └─ fixtures/
      └─ sample_stt.json
└─ scripts/
   └─ local_map_segments.py
```

---

## `pyproject.toml`
```toml
[project]
name = "selective-speaker-backend"
version = "0.1.0"
description = "FastAPI backend for diarization-only selective speaker transcription"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "pydantic>=2.7",
  "SQLAlchemy>=2.0",
  "psycopg[binary]>=3.2",
  "python-dotenv>=1.0",
  "alembic>=1.13",
  "httpx>=0.27",
  "python-multipart>=0.0.9",
  "loguru>=0.7",
]

[tool.uvicorn]
factory = true

[tool.pytest.ini_options]
pythonpath = ["app"]
```

---

## `.env.example`
```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/selective
ENV=dev
# Dev local storage root (for uploaded audio)
STORAGE_ROOT=./data
# Enrollment pad ms
PAD_MS=1000
# Minimum enrollment dominance ratio (0..1)
ENROLL_DOMINANCE=0.8
# Gap (ms) to merge adjacent user words into a segment
SEGMENT_GAP_MS=500
# Segment accept thresholds
SEGMENT_MIN_MS=1000
SEGMENT_MIN_CHARS=6
ASSEMBLYAI_WEBHOOK_SECRET=devsecret
```

---

## `docker-compose.yml`
```yaml
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
      POSTGRES_DB: selective
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

---

## `alembic.ini`
```ini
[alembic]
script_location = alembic
sqlalchemy.url = %(DATABASE_URL)s

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers = console
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers = console
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

> (Run `alembic init alembic` later for migration env; this `alembic.ini` is placeholder.)

---

## `app/config.py`
```python
from pydantic import BaseModel
import os

class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/selective")
    ENV: str = os.getenv("ENV", "dev")
    STORAGE_ROOT: str = os.getenv("STORAGE_ROOT", "./data")

    PAD_MS: int = int(os.getenv("PAD_MS", 1000))
    ENROLL_DOMINANCE: float = float(os.getenv("ENROLL_DOMINANCE", 0.8))
    SEGMENT_GAP_MS: int = int(os.getenv("SEGMENT_GAP_MS", 500))
    SEGMENT_MIN_MS: int = int(os.getenv("SEGMENT_MIN_MS", 1000))
    SEGMENT_MIN_CHARS: int = int(os.getenv("SEGMENT_MIN_CHARS", 6))

    ASSEMBLYAI_WEBHOOK_SECRET: str = os.getenv("ASSEMBLYAI_WEBHOOK_SECRET", "devsecret")

settings = Settings()
```

---

## `app/db.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

# Dependency for FastAPI
from contextlib import contextmanager

@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

---

## `app/models.py`
```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)  # Firebase UID
    display_name: Mapped[str | None] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    enrollments: Mapped[list[Enrollment]] = relationship(back_populates="user", cascade="all, delete")  # type: ignore

class Enrollment(Base):
    __tablename__ = "enrollments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    audio_url: Mapped[str] = mapped_column(String(512))
    duration_ms: Mapped[int] = mapped_column(Integer)
    phrase_text: Mapped[str | None] = mapped_column(Text)
    edit_distance: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="enrollments")  # type: ignore

class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    audio_url: Mapped[str] = mapped_column(String(512))
    device_id: Mapped[str | None] = mapped_column(String(128))
    start_ts: Mapped[datetime | None] = mapped_column(DateTime)
    end_ts: Mapped[datetime | None] = mapped_column(DateTime)
    gps_lat: Mapped[float | None] = mapped_column(Float)
    gps_lon: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Segment(Base):
    __tablename__ = "segments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.id"), index=True)
    speaker_label: Mapped[str] = mapped_column(String(64))
    start_ms: Mapped[int] = mapped_column(Integer)  # relative to original chunk (not concatenated file)
    end_ms: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    kept: Mapped[bool] = mapped_column(Boolean, default=True)

class Location(Base):
    __tablename__ = "locations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.id"), unique=True)
    address: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(64))
```

> Run `alembic` to generate the initial migration from these models.

---

## `app/schemas.py`
```python
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
```

---

## `app/storage.py` (dev local storage; swap for S3/GCS later)
```python
from pathlib import Path
from app.config import settings

ROOT = Path(settings.STORAGE_ROOT)
ROOT.mkdir(parents=True, exist_ok=True)

def local_path(url_or_rel: str) -> Path:
    # For dev, treat audio_url as relative path under STORAGE_ROOT
    p = ROOT / url_or_rel
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
```

---

## `app/utils/audio.py`
```python
from pathlib import Path
import wave

class WAVInfo:
    def __init__(self, path: Path):
        with wave.open(str(path), 'rb') as w:
            self.channels = w.getnchannels()
            self.samplerate = w.getframerate()
            self.frames = w.getnframes()
            self.duration_s = self.frames / float(self.samplerate)

    @property
    def duration_ms(self) -> int:
        return int(self.duration_s * 1000)
```

---

## `app/services/diarization_mapper.py`
```python
from collections import defaultdict
from typing import Any
from app.config import settings

# Expected STT words schema (per word):
# {"start": int_ms, "end": int_ms, "speaker": "SPEAKER_00", "confidence": float, "text": str}

class MapResult(dict):
    pass

def map_enrollment_anchored(stt_words: list[dict[str, Any]], enroll_ms: int) -> MapResult:
    PAD_MS = settings.PAD_MS
    ENROLL_DOM = settings.ENROLL_DOMINANCE
    GAP = settings.SEGMENT_GAP_MS
    MIN_MS = settings.SEGMENT_MIN_MS
    MIN_CHARS = settings.SEGMENT_MIN_CHARS

    # 1) Determine dominant label in enrollment window
    label_time: dict[str,int] = defaultdict(int)
    for w in stt_words:
        if w["start"] < enroll_ms:
            label_time[w["speaker"]] += (w["end"] - w["start"])
    if not label_time:
        return MapResult(status="indeterminate", reason="no_enrollment_words")

    user_label, dom_time = max(label_time.items(), key=lambda kv: kv[1])
    if dom_time < int(ENROLL_DOM * enroll_ms):
        return MapResult(status="indeterminate", reason="weak_enrollment_dominance", user_label=user_label)

    # 2) Collect words in CHUNK region for user label
    chunk_start = enroll_ms + PAD_MS
    user_words = [
        w for w in stt_words
        if w["speaker"] == user_label and w["start"] >= chunk_start
    ]

    # 3) Group contiguous words into segments
    segments: list[list[dict[str,Any]]] = []
    cur: list[dict[str,Any]] = []
    last_end = None
    for w in user_words:
        if last_end is None or (w["start"] - last_end) <= GAP:
            cur.append(w)
        else:
            segments.append(cur)
            cur = [w]
        last_end = w["end"]
    if cur:
        segments.append(cur)

    # 4) Filter segments and normalize times relative to original chunk
    kept: list[dict[str,Any]] = []
    for seg in segments:
        seg_start = seg[0]["start"] - chunk_start
        seg_end = seg[-1]["end"] - chunk_start
        dur = seg_end - seg_start
        text = " ".join(w["text"] for w in seg)
        if dur >= MIN_MS and len(text) >= MIN_CHARS:
            avg_conf = sum(w.get("confidence", 1.0) for w in seg) / len(seg)
            kept.append({
                "start_ms": int(seg_start),
                "end_ms": int(seg_end),
                "text": text,
                "avg_conf": float(avg_conf),
            })

    return MapResult(status="ok", user_label=user_label, kept=kept)
```

---

## `app/services/assemblyai_client.py`
```python
# Placeholder client. In prod, use httpx to POST audio, poll, and verify webhooks.
# This module defines the expected webhook payload shape consumed by routes/webhooks.py

from typing import Any, Dict

# Expected webhook payload minimal shape:
# {
#   "id": "transcript_id",
#   "metadata": {"user_id": 1, "chunk_id": 42, "enrollment_ms": 29000},
#   "words": [
#       {"start": 0, "end": 500, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "Hello"},
#       ...
#   ]
# }

def verify_signature(headers: Dict[str, str], body: bytes, secret: str) -> bool:
    # Implement HMAC verification using provider header values.
    # For dev skeleton, always return True.
    return True
```

---

## `app/services/geocoding.py`
```python
# Stub for reverse geocoding. In prod, call Google/Mapbox.
from typing import Optional, Tuple

def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    return f"Lat {lat:.5f}, Lon {lon:.5f}"
```

---

## `app/routes/enrollment.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import session_scope
from app import models, schemas

router = APIRouter(prefix="/enrollment", tags=["enrollment"])

@router.post("/complete")
def complete_enrollment(payload: schemas.EnrollmentCreate):
    with session_scope() as db:  # type: Session
        # Here you would verify Firebase JWT and map to user
        user = db.query(models.User).filter_by(uid="dev-uid").first()
        if not user:
            user = models.User(uid="dev-uid", display_name="Dev User")
            db.add(user)
            db.flush()
        e = models.Enrollment(
            user_id=user.id,
            audio_url=payload.audio_url,
            duration_ms=payload.duration_ms,
            phrase_text=payload.phrase_text,
            edit_distance=payload.edit_distance,
        )
        db.add(e)
        return {"status": "ok", "enrollment_id": e.id}
```

---

## `app/routes/chunks.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import session_scope
from app import models, schemas

router = APIRouter(prefix="/chunks", tags=["chunks"])

@router.post("/submit")
def submit_chunk(payload: schemas.ChunkSubmit):
    with session_scope() as db:
        user = db.query(models.User).filter_by(uid="dev-uid").first()
        if not user:
            raise RuntimeError("Dev user not found; create enrollment first.")
        c = models.Chunk(
            user_id=user.id,
            audio_url=payload.audio_url,
            device_id=payload.device_id,
            start_ts=payload.start_ts,
            end_ts=payload.end_ts,
            gps_lat=payload.gps_lat,
            gps_lon=payload.gps_lon,
        )
        db.add(c)
        db.flush()
        # In prod: enqueue STT job with metadata (user_id, chunk_id, enrollment_ms)
        return {"status": "queued", "chunk_id": c.id}
```

---

## `app/routes/utterances.py`
```python
from fastapi import APIRouter
from sqlalchemy.orm import Session
from app.db import session_scope
from app import models, schemas

router = APIRouter(prefix="/utterances", tags=["utterances"])

@router.get("")
def list_utterances(limit: int = 50, cursor: int | None = None):
    with session_scope() as db:
        # For demo, we flatten kept segments as bubbles with chunk/device/address
        q = db.query(models.Segment, models.Chunk).join(models.Chunk, models.Chunk.id == models.Segment.chunk_id)
        q = q.order_by(models.Segment.id.desc()).limit(limit)
        rows = q.all()
        items: list[schemas.UtteranceBubble] = []
        for seg, ch in rows:
            # Resolve address if any
            addr_row = db.query(models.Location).filter_by(chunk_id=ch.id).first()
            items.append(schemas.UtteranceBubble(
                chunk_id=ch.id,
                start_ms=seg.start_ms,
                end_ms=seg.end_ms,
                text=seg.text,
                device_id=ch.device_id,
                timestamp=ch.end_ts or ch.start_ts,
                address=addr_row.address if addr_row else None,
            ))
        return {"items": [i.model_dump() for i in items]}
```

---

## `app/routes/webhooks.py`
```python
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
from app.db import session_scope
from app import models
from app.config import settings
from app.services.diarization_mapper import map_enrollment_anchored
from app.services.assemblyai_client import verify_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/assemblyai")
async def assemblyai_webhook(request: Request):
    body = await request.body()
    if not verify_signature(dict(request.headers), body, settings.ASSEMBLYAI_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    words = payload.get("words", [])
    md = payload.get("metadata", {})
    user_id = md.get("user_id")
    chunk_id = md.get("chunk_id")
    enrollment_ms = md.get("enrollment_ms")

    if not (user_id and chunk_id and enrollment_ms is not None):
        raise HTTPException(status_code=400, detail="Missing metadata")

    result = map_enrollment_anchored(words, enroll_ms=int(enrollment_ms))
    if result.get("status") != "ok":
        return {"status": "ignored", "reason": result.get("reason", "indeterminate")}

    kept = result["kept"]

    with session_scope() as db:
        # Persist kept segments
        for seg in kept:
            db.add(models.Segment(
                chunk_id=chunk_id,
                speaker_label=result.get("user_label", "USER"),
                start_ms=seg["start_ms"],
                end_ms=seg["end_ms"],
                text=seg["text"],
                confidence=seg.get("avg_conf"),
                kept=True,
            ))
    return {"status": "ok", "kept_count": len(kept)}
```

---

## `app/main.py`
```python
from fastapi import FastAPI
from app.routes import enrollment, chunks, utterances, webhooks

app = FastAPI(title="Selective Speaker Backend")

app.include_router(enrollment.router)
app.include_router(chunks.router)
app.include_router(utterances.router)
app.include_router(webhooks.router)

# Uvicorn: uvicorn app.main:app --reload
```

---

## `tests/test_diarization_mapper.py`
```python
from app.services.diarization_mapper import map_enrollment_anchored

# Synthetic example: enrollment occupies 3000ms with SPEAKER_00; chunk begins at 4000ms

def test_mapper_keeps_user_segments():
    words = []
    # Enrollment (0..3000):
    words += [
        {"start": 0, "end": 500, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "This"},
        {"start": 500, "end": 1000, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "is"},
        {"start": 1000, "end": 1500, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "my"},
        {"start": 1500, "end": 2200, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "voice"},
        {"start": 2200, "end": 3000, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "sample"},
    ]
    # PAD 1000ms (silence) 3000..4000
    # Chunk words (>=4000): alternating speakers
    words += [
        {"start": 4100, "end": 4600, "speaker": "SPEAKER_00", "confidence": 0.85, "text": "Hello"},
        {"start": 4700, "end": 5300, "speaker": "SPEAKER_01", "confidence": 0.85, "text": "(other)"},
        {"start": 5400, "end": 6000, "speaker": "SPEAKER_00", "confidence": 0.85, "text": "world"},
        {"start": 6500, "end": 7000, "speaker": "SPEAKER_00", "confidence": 0.85, "text": "again"},
    ]
    res = map_enrollment_anchored(words, enroll_ms=3000)
    assert res["status"] == "ok"
    kept = res["kept"]
    # Expect 2 segments ("Hello" + "world again" merged with <=500ms gaps)
    assert len(kept) >= 1
    # Sanity: start times should be relative to chunk start (4000ms removed)
    assert kept[0]["start_ms"] >= 0
```
```

---

## `scripts/local_map_segments.py`
```python
"""
Local test harness:
- Takes enrollment duration (ms), and a JSON file with STT words (AssemblyAI-like)
- Runs the mapper and prints kept segments.

Usage:
  python scripts/local_map_segments.py --enroll-ms 30000 --stt tests/fixtures/sample_stt.json
"""
import json
import argparse
from app.services.diarization_mapper import map_enrollment_anchored

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--enroll-ms", type=int, required=True)
    parser.add_argument("--stt", type=str, required=True)
    args = parser.parse_args()

    with open(args.stt, "r") as f:
        data = json.load(f)

    words = data["words"] if isinstance(data, dict) and "words" in data else data
    res = map_enrollment_anchored(words, enroll_ms=args.enroll_ms)
    print(json.dumps(res, indent=2))
```

---

## `README.md`
```markdown
# Selective Speaker Backend (FastAPI)

Diarization-only selective speaker pipeline using enrollment-anchored mapping.

## Quickstart (dev)

1. **Run Postgres**

```bash
docker compose up -d db
```

2. **Create venv & install**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

3. **Set env**

```bash
cp .env.example .env
```

4. **Create tables (dev)**

```python
# quick and dirty (use Alembic later)
python -c "from app.db import Base, engine; import app.models as m; Base.metadata.create_all(engine)"
```

5. **Run API**

```bash
uvicorn app.main:app --reload
```

6. **Test mapper locally**

```bash
python scripts/local_map_segments.py --enroll-ms 3000 --stt tests/fixtures/sample_stt.json
```

## Notes
- Replace `verify_signature` with real HMAC verification.
- Swap `storage.py` for S3/GCS when moving to cloud; keep audio URLs as keys.
- Implement geocoding in `services/geocoding.py` (Google/Mapbox).
- In production, `/chunks/submit` should enqueue an STT job and include metadata `{user_id, chunk_id, enrollment_ms}` so the webhook can map spans.
```

