from fastapi import APIRouter, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from app.db import session_scope
from app import models, schemas

router = APIRouter(prefix="/utterances", tags=["utterances"])


@router.get("")
def list_utterances(
    limit: int = Query(50, ge=1, le=200),
    before_id: Optional[int] = None
):
    """
    List user's utterances (kept segments) in timeline format.
    
    Returns segments as speech bubbles with timestamps and locations,
    similar to a messaging app interface but single-speaker.
    
    Args:
        limit: Maximum number of utterances to return (1-200)
        before_id: Cursor for pagination - return utterances before this segment ID
    
    Returns:
        List of utterance bubbles with text, timestamps, and locations
    """
    with session_scope() as db:
        # For demo, we flatten kept segments as bubbles with chunk/device/address
        # Join segments with chunks to get metadata
        query = (
            db.query(models.Segment, models.Chunk)
            .join(models.Chunk, models.Chunk.id == models.Segment.chunk_id)
            .filter(models.Segment.kept == True)
        )
        
        if before_id is not None:
            query = query.filter(models.Segment.id < before_id)
        
        query = query.order_by(desc(models.Segment.id)).limit(limit)
        rows = query.all()
        
        items: List[schemas.UtteranceBubble] = []
        for seg, chunk in rows:
            # Resolve address if available
            addr_row = db.query(models.Location).filter_by(chunk_id=chunk.id).first()
            
            items.append(schemas.UtteranceBubble(
                chunk_id=chunk.id,
                start_ms=seg.start_ms,
                end_ms=seg.end_ms,
                text=seg.text,
                device_id=chunk.device_id,
                timestamp=chunk.end_ts or chunk.start_ts or chunk.created_at,
                address=addr_row.address if addr_row else None,
            ))
        
        return {
            "items": [item.model_dump() for item in items],
            "count": len(items),
            "has_more": len(items) == limit
        }


@router.get("/search")
def search_utterances(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Search utterances by text content.
    
    In production, this would use full-text search (PostgreSQL FTS)
    or Elasticsearch/OpenSearch for better performance.
    
    Args:
        q: Search query
        limit: Maximum results to return
    
    Returns:
        Matching utterances
    """
    with session_scope() as db:
        # Simple LIKE search (use FTS or Elasticsearch in production)
        query = (
            db.query(models.Segment, models.Chunk)
            .join(models.Chunk, models.Chunk.id == models.Segment.chunk_id)
            .filter(models.Segment.kept == True)
            .filter(models.Segment.text.ilike(f"%{q}%"))
            .order_by(desc(models.Segment.id))
            .limit(limit)
        )
        
        rows = query.all()
        items: List[schemas.UtteranceBubble] = []
        
        for seg, chunk in rows:
            addr_row = db.query(models.Location).filter_by(chunk_id=chunk.id).first()
            
            items.append(schemas.UtteranceBubble(
                chunk_id=chunk.id,
                start_ms=seg.start_ms,
                end_ms=seg.end_ms,
                text=seg.text,
                device_id=chunk.device_id,
                timestamp=chunk.end_ts or chunk.start_ts or chunk.created_at,
                address=addr_row.address if addr_row else None,
            ))
        
        return {
            "items": [item.model_dump() for item in items],
            "count": len(items),
            "query": q
        }

