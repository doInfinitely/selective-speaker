#!/usr/bin/env python3
"""
Local test harness for diarization mapper.

Takes enrollment duration (ms) and a JSON file with STT words (AssemblyAI-like format)
and runs the enrollment-anchored mapper to show kept segments.

Usage:
    python scripts/local_map_segments.py --enroll-ms 30000 --stt tests/fixtures/sample_stt.json
"""

import json
import argparse
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.diarization_mapper import map_enrollment_anchored


def main():
    parser = argparse.ArgumentParser(
        description="Test enrollment-anchored diarization mapper"
    )
    parser.add_argument(
        "--enroll-ms",
        type=int,
        required=True,
        help="Duration of enrollment audio in milliseconds"
    )
    parser.add_argument(
        "--stt",
        type=str,
        required=True,
        help="Path to JSON file with STT words"
    )
    args = parser.parse_args()

    # Load STT data
    with open(args.stt, "r") as f:
        data = json.load(f)

    # Handle both {"words": [...]} and [...] formats
    words = data["words"] if isinstance(data, dict) and "words" in data else data

    # Run mapper
    result = map_enrollment_anchored(words, enroll_ms=args.enroll_ms)

    # Pretty print results
    print(json.dumps(result, indent=2))

    # Summary
    if result.get("status") == "ok":
        kept = result.get("kept", [])
        print(f"\n✓ Successfully mapped {len(kept)} segment(s)")
        print(f"User label: {result.get('user_label')}")
        
        if kept:
            print("\nKept segments:")
            for i, seg in enumerate(kept, 1):
                duration = (seg["end_ms"] - seg["start_ms"]) / 1000
                print(f"  {i}. [{seg['start_ms']}ms - {seg['end_ms']}ms] ({duration:.1f}s)")
                print(f"     \"{seg['text']}\"")
                print(f"     Confidence: {seg.get('avg_conf', 0):.2f}")
    else:
        print(f"\n✗ Mapping failed: {result.get('reason')}")


if __name__ == "__main__":
    main()

