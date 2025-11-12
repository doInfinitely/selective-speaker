from collections import defaultdict
from typing import Any, List, Dict
from app.config import settings

# Expected STT words schema (per word):
# {"start": int_ms, "end": int_ms, "speaker": "SPEAKER_00", "confidence": float, "text": str}


class MapResult(dict):
    """Result dictionary from enrollment-anchored mapping"""
    pass


def map_enrollment_anchored(stt_words: List[Dict[str, Any]], enroll_ms: int) -> MapResult:
    """
    Maps diarized words to user segments using enrollment-anchored approach.
    
    Args:
        stt_words: List of word dictionaries from STT with diarization
        enroll_ms: Duration of enrollment audio in milliseconds
    
    Returns:
        MapResult with status='ok' and kept segments, or status='indeterminate' with reason
    """
    PAD_MS = settings.PAD_MS
    ENROLL_DOM = settings.ENROLL_DOMINANCE
    GAP = settings.SEGMENT_GAP_MS
    MIN_MS = settings.SEGMENT_MIN_MS
    MIN_CHARS = settings.SEGMENT_MIN_CHARS

    # 1) Determine dominant label in enrollment window
    label_time: Dict[str, int] = defaultdict(int)
    for w in stt_words:
        if w["start"] < enroll_ms:
            label_time[w["speaker"]] += (w["end"] - w["start"])
    
    if not label_time:
        return MapResult(status="indeterminate", reason="no_enrollment_words")

    user_label, dom_time = max(label_time.items(), key=lambda kv: kv[1])
    
    # Calculate percentages for debugging
    total_time = sum(label_time.values())
    speaker_percentages = {
        spk: (time / total_time * 100) if total_time > 0 else 0 
        for spk, time in label_time.items()
    }
    
    from loguru import logger
    logger.info(f"Enrollment region analysis (0-{enroll_ms}ms):")
    logger.info(f"  Total speech time: {total_time}ms / {enroll_ms}ms ({total_time/enroll_ms*100:.1f}%)")
    for spk, pct in sorted(speaker_percentages.items(), key=lambda x: -x[1]):
        logger.info(f"  {spk}: {label_time[spk]}ms ({pct:.1f}%)")
    logger.info(f"  Dominant: {user_label} ({dom_time}ms, {dom_time/enroll_ms*100:.1f}%)")
    logger.info(f"  Required: {ENROLL_DOM*100:.0f}% of enrollment duration")
    
    if dom_time < int(ENROLL_DOM * enroll_ms):
        return MapResult(
            status="indeterminate", 
            reason="weak_enrollment_dominance", 
            user_label=user_label,
            debug={
                "speaker_percentages": speaker_percentages,
                "dominant_speaker": user_label,
                "dominant_percentage": dom_time/enroll_ms*100,
                "required_percentage": ENROLL_DOM*100
            }
        )

    # 2) Collect words in CHUNK region for user label
    chunk_start = enroll_ms + PAD_MS
    
    # Debug: Show all speakers in chunk region
    chunk_words_by_speaker: Dict[str, int] = defaultdict(int)
    for w in stt_words:
        if w["start"] >= chunk_start:
            chunk_words_by_speaker[w["speaker"]] += 1
    
    logger.info(f"Chunk region analysis ({chunk_start}ms onwards):")
    logger.info(f"  Total words in chunk: {sum(chunk_words_by_speaker.values())}")
    for spk, count in sorted(chunk_words_by_speaker.items(), key=lambda x: -x[1]):
        logger.info(f"  {spk}: {count} words")
    # Determine which speaker to accept in chunk
    # Option 1: Use enrollment label (original approach, but suffers from label drift)
    # Option 2: Use majority speaker in chunk (more robust to label drift)
    if settings.USE_MAJORITY_SPEAKER and chunk_words_by_speaker:
        # Use the most common speaker in chunk region
        chunk_user_label = max(chunk_words_by_speaker.items(), key=lambda x: x[1])[0]
        logger.info(f"  Enrollment speaker was: {user_label}")
        logger.info(f"  Using MAJORITY speaker from chunk: {chunk_user_label}")
        actual_user_label = chunk_user_label
    else:
        # Use enrollment speaker label (original behavior)
        logger.info(f"  Looking for user speaker: {user_label}")
        actual_user_label = user_label
    
    user_words = [
        w for w in stt_words
        if w["speaker"] == actual_user_label and w["start"] >= chunk_start
    ]
    
    logger.info(f"  Found {len(user_words)} words from {actual_user_label} in chunk region")

    # 3) Group contiguous words into segments
    segments: List[List[Dict[str, Any]]] = []
    cur: List[Dict[str, Any]] = []
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
    kept: List[Dict[str, Any]] = []
    filtered_out = 0
    
    logger.info(f"Segment filtering (min {MIN_MS}ms, min {MIN_CHARS} chars):")
    logger.info(f"  Found {len(segments)} raw segments before filtering")
    
    for i, seg in enumerate(segments):
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
            logger.info(f"  ✓ Segment {i+1}: {dur}ms, {len(text)} chars - \"{text[:50]}...\"")
        else:
            filtered_out += 1
            logger.info(f"  ✗ Segment {i+1}: {dur}ms, {len(text)} chars - FILTERED (too short)")
    
    logger.info(f"  Result: {len(kept)} kept, {filtered_out} filtered out")

    # Return the actual speaker label used (may differ from enrollment label if USE_MAJORITY_SPEAKER=True)
    return MapResult(status="ok", user_label=actual_user_label, kept=kept)

