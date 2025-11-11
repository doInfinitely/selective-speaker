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
    if dom_time < int(ENROLL_DOM * enroll_ms):
        return MapResult(
            status="indeterminate", 
            reason="weak_enrollment_dominance", 
            user_label=user_label
        )

    # 2) Collect words in CHUNK region for user label
    chunk_start = enroll_ms + PAD_MS
    user_words = [
        w for w in stt_words
        if w["speaker"] == user_label and w["start"] >= chunk_start
    ]

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

