"""
Audio extraction utilities for extracting segments from larger audio files.
"""

from pathlib import Path
from typing import BinaryIO
import wave
import struct
from io import BytesIO
from loguru import logger


def extract_audio_segment(
    input_path: Path,
    start_ms: int,
    end_ms: int,
    output_format: str = "wav",
    amplify: float = 6.0
) -> bytes:
    """
    Extract a segment from an audio file and return as bytes.
    
    Args:
        input_path: Path to input WAV file
        start_ms: Start time in milliseconds
        end_ms: End time in milliseconds
        output_format: Output format (only 'wav' supported for now)
        amplify: Amplification factor (default 6.0 = 6x louder)
    
    Returns:
        Audio segment as bytes
    """
    logger.info(f"Extracting segment [{start_ms}ms - {end_ms}ms] from {input_path} (amplify={amplify}x)")
    
    # Open input file
    with wave.open(str(input_path), 'rb') as wav_in:
        # Get audio parameters
        n_channels = wav_in.getnchannels()
        sample_width = wav_in.getsampwidth()
        framerate = wav_in.getframerate()
        
        # Calculate frame positions
        start_frame = int(start_ms * framerate / 1000)
        end_frame = int(end_ms * framerate / 1000)
        n_frames = end_frame - start_frame
        
        # Seek to start position and read frames
        wav_in.setpos(start_frame)
        audio_data = wav_in.readframes(n_frames)
    
    # Amplify audio if requested
    if amplify != 1.0:
        audio_data = _amplify_audio(audio_data, sample_width, amplify)
    
    # Create output WAV in memory
    output_buffer = BytesIO()
    with wave.open(output_buffer, 'wb') as wav_out:
        wav_out.setnchannels(n_channels)
        wav_out.setsampwidth(sample_width)
        wav_out.setframerate(framerate)
        wav_out.writeframes(audio_data)
    
    # Get bytes
    output_bytes = output_buffer.getvalue()
    
    logger.info(f"Extracted segment: {len(output_bytes)} bytes, duration={(end_ms-start_ms)}ms")
    
    return output_bytes


def _amplify_audio(audio_data: bytes, sample_width: int, factor: float) -> bytes:
    """
    Amplify audio data by multiplying samples.
    
    Args:
        audio_data: Raw audio bytes
        sample_width: Bytes per sample (1=8bit, 2=16bit)
        factor: Amplification factor
    
    Returns:
        Amplified audio data
    """
    if sample_width == 2:  # 16-bit audio (most common)
        # Unpack as signed 16-bit integers
        samples = struct.unpack(f'<{len(audio_data)//2}h', audio_data)
        
        # Amplify and clamp to prevent clipping
        amplified = []
        for sample in samples:
            new_sample = int(sample * factor)
            # Clamp to 16-bit range
            new_sample = max(-32768, min(32767, new_sample))
            amplified.append(new_sample)
        
        # Pack back to bytes
        return struct.pack(f'<{len(amplified)}h', *amplified)
    else:
        # For other sample widths, just return unchanged
        logger.warning(f"Amplification not supported for sample_width={sample_width}")
        return audio_data


def get_audio_duration_ms(audio_path: Path) -> int:
    """
    Get duration of audio file in milliseconds.
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        Duration in milliseconds
    """
    with wave.open(str(audio_path), 'rb') as wav:
        frames = wav.getnframes()
        rate = wav.getframerate()
        duration_ms = int((frames / rate) * 1000)
    
    return duration_ms

