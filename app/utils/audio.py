"""
Audio utility functions for processing WAV files.
"""

from pathlib import Path
import wave


class WAVInfo:
    """Extract information from WAV audio files."""
    
    def __init__(self, path: Path):
        """
        Read WAV file and extract metadata.
        
        Args:
            path: Path to WAV file
        """
        with wave.open(str(path), 'rb') as w:
            self.channels = w.getnchannels()
            self.samplerate = w.getframerate()
            self.frames = w.getnframes()
            self.duration_s = self.frames / float(self.samplerate)

    @property
    def duration_ms(self) -> int:
        """Duration in milliseconds."""
        return int(self.duration_s * 1000)


def concatenate_audio_files(
    enrollment_path: Path,
    chunk_path: Path,
    output_path: Path,
    pad_ms: int = 1000
) -> WAVInfo:
    """
    Concatenate enrollment audio + silence pad + chunk audio.
    
    This creates the file structure needed for enrollment-anchored diarization:
    [enrollment audio] + [silence padding] + [chunk to analyze]
    
    Args:
        enrollment_path: Path to enrollment WAV file
        chunk_path: Path to chunk WAV file
        output_path: Path for output concatenated file
        pad_ms: Milliseconds of silence to insert between files
    
    Returns:
        WAVInfo object for the concatenated file
    """
    # TODO: Implement actual audio concatenation
    # This would:
    # 1. Read enrollment WAV
    # 2. Generate silence frames (pad_ms worth)
    # 3. Read chunk WAV
    # 4. Write all frames to output_path
    # 5. Return WAVInfo of output file
    
    raise NotImplementedError("Audio concatenation not yet implemented")

