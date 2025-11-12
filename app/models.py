from sqlalchemy import Integer, String, Boolean, ForeignKey, Float, DateTime, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional, List
from app.db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)  # Firebase UID
    display_name: Mapped[Optional[str]] = mapped_column(String(128))
    email: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="user", cascade="all, delete")


class Enrollment(Base):
    __tablename__ = "enrollments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    audio_url: Mapped[str] = mapped_column(String(512))
    duration_ms: Mapped[int] = mapped_column(Integer)
    phrase_text: Mapped[Optional[str]] = mapped_column(Text)
    edit_distance: Mapped[Optional[int]] = mapped_column(Integer)
    embedding_vector: Mapped[Optional[str]] = mapped_column(Text)  # JSON-encoded numpy array
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="enrollments")


class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    audio_url: Mapped[str] = mapped_column(String(512))
    device_id: Mapped[Optional[str]] = mapped_column(String(128))
    start_ts: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end_ts: Mapped[Optional[datetime]] = mapped_column(DateTime)
    gps_lat: Mapped[Optional[float]] = mapped_column(Float)
    gps_lon: Mapped[Optional[float]] = mapped_column(Float)
    transcript_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)  # AssemblyAI transcript ID
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Segment(Base):
    __tablename__ = "segments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.id"), index=True)
    speaker_label: Mapped[str] = mapped_column(String(64))
    start_ms: Mapped[int] = mapped_column(Integer)  # relative to original chunk (not concatenated file)
    end_ms: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    kept: Mapped[bool] = mapped_column(Boolean, default=True)


class Location(Base):
    __tablename__ = "locations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.id"), unique=True)
    address: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(64))

