"""
Audio utility functions for processing WAV files.
"""

from pathlib import Path
import wave
import struct
from typing import Optional
from app.config import settings


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
            self.sampwidth = w.getsampwidth()

    @property
    def duration_ms(self) -> int:
        """Duration in milliseconds."""
        return int(self.duration_s * 1000)


def generate_silence(duration_ms: int, sample_rate: int = 16000, channels: int = 1, sampwidth: int = 2) -> bytes:
    """
    Generate silence audio data.
    
    Args:
        duration_ms: Duration of silence in milliseconds
        sample_rate: Sample rate in Hz (default 16000)
        channels: Number of channels (default 1 for mono)
        sampwidth: Sample width in bytes (default 2 for 16-bit)
    
    Returns:
        Raw audio bytes of silence
    """
    num_samples = int((duration_ms / 1000.0) * sample_rate)
    # Generate silence (zeros)
    silence_data = struct.pack('h' * num_samples * channels, *([0] * (num_samples * channels)))
    return silence_data


def concatenate_audio_files(
    enrollment_path: Path,
    chunk_path: Path,
    output_path: Path,
    pad_ms: Optional[int] = None
) -> WAVInfo:
    """
    Concatenate enrollment audio + silence pad + chunk audio.
    
    This creates the file structure needed for enrollment-anchored diarization:
    [enrollment audio] + [silence padding] + [chunk to analyze]
    
    Args:
        enrollment_path: Path to enrollment WAV file
        chunk_path: Path to chunk WAV file
        output_path: Path for output concatenated file
        pad_ms: Milliseconds of silence to insert between files (default from settings)
    
    Returns:
        WAVInfo object for the concatenated file
    
    Raises:
        ValueError: If audio files have incompatible parameters
    """
    if pad_ms is None:
        pad_ms = settings.PAD_MS
    
    # Read enrollment audio
    with wave.open(str(enrollment_path), 'rb') as enroll_wav:
        enroll_params = enroll_wav.getparams()
        enroll_data = enroll_wav.readframes(enroll_wav.getnframes())
    
    # Read chunk audio
    with wave.open(str(chunk_path), 'rb') as chunk_wav:
        chunk_params = chunk_wav.getparams()
        chunk_data = chunk_wav.readframes(chunk_wav.getnframes())
    
    # Verify compatibility
    if enroll_params.nchannels != chunk_params.nchannels:
        raise ValueError(
            f"Channel mismatch: enrollment has {enroll_params.nchannels} channels, "
            f"chunk has {chunk_params.nchannels} channels"
        )
    
    if enroll_params.framerate != chunk_params.framerate:
        raise ValueError(
            f"Sample rate mismatch: enrollment is {enroll_params.framerate}Hz, "
            f"chunk is {chunk_params.framerate}Hz"
        )
    
    if enroll_params.sampwidth != chunk_params.sampwidth:
        raise ValueError(
            f"Sample width mismatch: enrollment is {enroll_params.sampwidth} bytes, "
            f"chunk is {chunk_params.sampwidth} bytes"
        )
    
    # Generate silence padding
    silence_data = generate_silence(
        duration_ms=pad_ms,
        sample_rate=enroll_params.framerate,
        channels=enroll_params.nchannels,
        sampwidth=enroll_params.sampwidth
    )
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write concatenated audio
    with wave.open(str(output_path), 'wb') as out_wav:
        out_wav.setparams(enroll_params)
        out_wav.writeframes(enroll_data)
        out_wav.writeframes(silence_data)
        out_wav.writeframes(chunk_data)
    
    return WAVInfo(output_path)

