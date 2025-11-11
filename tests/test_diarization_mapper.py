"""
Tests for the diarization mapper service.
"""

from app.services.diarization_mapper import map_enrollment_anchored


def test_mapper_keeps_user_segments():
    """
    Test that mapper correctly identifies and keeps user segments.
    
    Synthetic example:
    - Enrollment occupies 0-3000ms with SPEAKER_00 dominant
    - Silence pad 3000-4000ms
    - Chunk begins at 4000ms with alternating speakers
    """
    words = []
    
    # Enrollment (0..3000ms): SPEAKER_00 dominates
    words += [
        {"start": 0, "end": 500, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "This"},
        {"start": 500, "end": 1000, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "is"},
        {"start": 1000, "end": 1500, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "my"},
        {"start": 1500, "end": 2200, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "voice"},
        {"start": 2200, "end": 3000, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "sample"},
    ]
    
    # PAD 1000ms (silence) 3000..4000
    
    # Chunk words (>=4000ms): alternating speakers
    words += [
        {"start": 4100, "end": 4600, "speaker": "SPEAKER_00", "confidence": 0.85, "text": "Hello"},
        {"start": 4700, "end": 5300, "speaker": "SPEAKER_01", "confidence": 0.85, "text": "(other)"},
        {"start": 5400, "end": 6000, "speaker": "SPEAKER_00", "confidence": 0.85, "text": "world"},
        {"start": 6500, "end": 7000, "speaker": "SPEAKER_00", "confidence": 0.85, "text": "again"},
    ]
    
    res = map_enrollment_anchored(words, enroll_ms=3000)
    
    # Should succeed
    assert res["status"] == "ok"
    assert res["user_label"] == "SPEAKER_00"
    
    kept = res["kept"]
    # Expect segments containing "world", "again" (SPEAKER_00 in chunk region)
    # "Hello" is too short (500ms < 1000ms minimum) so it gets filtered
    # Should NOT contain "(other)" (SPEAKER_01)
    assert len(kept) >= 1
    
    # Sanity: start times should be relative to chunk start (4000ms removed)
    assert kept[0]["start_ms"] >= 0
    
    # Check that text contains user's words but not other speaker
    all_text = " ".join(seg["text"] for seg in kept)
    # Note: "Hello" is filtered out due to being too short after gap
    assert "world" in all_text
    assert "again" in all_text
    assert "(other)" not in all_text


def test_mapper_rejects_weak_enrollment():
    """Test that mapper rejects when enrollment speaker is not dominant."""
    words = [
        # Enrollment region (0-3000ms) but SPEAKER_01 dominates
        {"start": 0, "end": 500, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "I"},
        {"start": 500, "end": 2500, "speaker": "SPEAKER_01", "confidence": 0.9, "text": "someone else talking"},
        {"start": 2500, "end": 3000, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "me"},
    ]
    
    res = map_enrollment_anchored(words, enroll_ms=3000)
    
    # Should be indeterminate due to weak dominance
    assert res["status"] == "indeterminate"
    assert "dominance" in res.get("reason", "").lower()


def test_mapper_handles_no_user_speech_in_chunk():
    """Test when enrollment succeeds but no user speech in chunk."""
    words = [
        # Strong enrollment
        {"start": 0, "end": 3000, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "enrollment text"},
        # Chunk has only other speakers
        {"start": 4100, "end": 5000, "speaker": "SPEAKER_01", "confidence": 0.85, "text": "other person"},
    ]
    
    res = map_enrollment_anchored(words, enroll_ms=3000)
    
    # Should succeed but with no kept segments
    assert res["status"] == "ok"
    assert len(res["kept"]) == 0


def test_mapper_filters_short_segments():
    """Test that very short segments are filtered out."""
    words = [
        # Good enrollment
        {"start": 0, "end": 3000, "speaker": "SPEAKER_00", "confidence": 0.9, "text": "enrollment"},
        # Very short utterance in chunk (< 1000ms and < 6 chars)
        {"start": 4100, "end": 4300, "speaker": "SPEAKER_00", "confidence": 0.85, "text": "ok"},
        # Longer valid utterance
        {"start": 5000, "end": 6500, "speaker": "SPEAKER_00", "confidence": 0.85, "text": "this message is valid"},
    ]
    
    res = map_enrollment_anchored(words, enroll_ms=3000)
    
    assert res["status"] == "ok"
    kept = res["kept"]
    
    # Should only keep the longer segment
    assert len(kept) == 1
    assert "message" in kept[0]["text"]
    assert kept[0]["text"] == "this message is valid"
    # The "ok" should be filtered out
    assert "ok" not in kept[0]["text"]

