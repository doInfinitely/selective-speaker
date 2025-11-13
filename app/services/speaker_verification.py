"""
Speaker verification using embeddings.

This is the CORRECT approach - compare acoustic fingerprints, not arbitrary labels.
"""

import torch
import torchaudio
from pathlib import Path
from typing import Dict, Optional
import numpy as np
from loguru import logger

# Lazy load the inference pipeline to avoid startup overhead
_inference_pipeline = None


def get_inference_pipeline():
    """Lazy load the speaker embedding inference pipeline."""
    global _inference_pipeline
    
    if _inference_pipeline is None:
        from app.config import settings
        
        logger.info("Loading speaker embedding inference pipeline (pyannote/embedding)...")
        
        # Require HuggingFace token
        if not settings.HUGGINGFACE_TOKEN:
            raise ValueError(
                "HUGGINGFACE_TOKEN not set. Please:\n"
                "1. Visit https://hf.co/pyannote/embedding and accept terms\n"
                "2. Create token at https://hf.co/settings/tokens\n"
                "3. Add HUGGINGFACE_TOKEN=your_token to .env"
            )
        
        # Login to HuggingFace hub first
        from huggingface_hub import login
        login(token=settings.HUGGINGFACE_TOKEN)
        
        # Use Inference API instead of raw Model (handles version mismatches better)
        from pyannote.audio import Inference
        _inference_pipeline = Inference("pyannote/embedding")
        
        logger.info("Speaker embedding inference pipeline loaded successfully")
    
    return _inference_pipeline


def extract_embedding(audio_path: Path) -> np.ndarray:
    """
    Extract speaker embedding from audio file.
    
    Args:
        audio_path: Path to audio file (WAV format)
    
    Returns:
        Embedding vector as numpy array (typically 512 dimensions)
    """
    inference = get_inference_pipeline()
    
    logger.info(f"Extracting embedding from {audio_path}")
    
    # Load audio manually (pyannote's audio loading is broken on Railway)
    import soundfile as sf
    import torch
    
    waveform, sample_rate = sf.read(str(audio_path))
    
    # Convert to torch tensor and ensure correct shape (channel, time)
    if waveform.ndim == 1:
        # Mono audio - add channel dimension
        waveform_tensor = torch.from_numpy(waveform).unsqueeze(0).float()
    else:
        # Stereo - take first channel and add dimension
        waveform_tensor = torch.from_numpy(waveform[:, 0]).unsqueeze(0).float()
    
    logger.debug(f"Loaded audio: shape={waveform_tensor.shape}, sample_rate={sample_rate}")
    
    # Create audio dict that pyannote expects
    audio_dict = {
        "waveform": waveform_tensor,
        "sample_rate": sample_rate
    }
    
    # Use pyannote Inference API with preloaded audio
    # Returns temporal embeddings (one per sliding window)
    temporal_embeddings = inference(audio_dict)
    
    # Convert to numpy
    embeddings_array = np.array(temporal_embeddings)
    logger.debug(f"Temporal embeddings shape: {embeddings_array.shape}")
    
    # Average across time dimension to get single embedding
    if embeddings_array.ndim == 2:
        # Shape is (num_windows, embedding_dim) - average across windows
        embedding_np = np.mean(embeddings_array, axis=0)
        logger.debug(f"Averaged {embeddings_array.shape[0]} temporal windows")
    else:
        # Already single embedding
        embedding_np = embeddings_array.squeeze()
    
    logger.debug(f"Before normalization - first 5 values: {embedding_np[:5]}")
    logger.debug(f"Before normalization - norm: {np.linalg.norm(embedding_np):.6f}")
    
    # Normalize
    embedding_np = embedding_np / np.linalg.norm(embedding_np)
    
    logger.debug(f"After normalization - first 5 values: {embedding_np[:5]}")
    logger.info(f"Extracted embedding: shape={embedding_np.shape}, mean={np.mean(embedding_np):.4f}, std={np.std(embedding_np):.4f}")
    
    return embedding_np


def extract_embedding_from_segment(audio_path: Path, start_ms: int, end_ms: int, speaker_label: str = "?") -> np.ndarray:
    """
    Extract speaker embedding from a specific segment of audio.
    
    Args:
        audio_path: Path to audio file
        start_ms: Start time in milliseconds
        end_ms: End time in milliseconds
    
    Returns:
        Embedding vector as numpy array
    """
    inference = get_inference_pipeline()
    
    logger.info(f"Extracting embedding for speaker {speaker_label} from {audio_path} [{start_ms}ms-{end_ms}ms]")
    
    # Create a pyannote Segment and use crop parameter
    from pyannote.core import Segment
    segment = Segment(start_ms / 1000.0, end_ms / 1000.0)
    
    # Extract embedding for this specific segment (returns temporal embeddings)
    temporal_embeddings = inference.crop(str(audio_path), segment)
    
    # Convert to numpy
    embeddings_array = np.array(temporal_embeddings)
    logger.debug(f"  Speaker {speaker_label} temporal shape: {embeddings_array.shape}")
    
    # Average across time dimension to get single embedding
    if embeddings_array.ndim == 2:
        # Shape is (num_windows, embedding_dim) - average across windows
        embedding_np = np.mean(embeddings_array, axis=0)
        logger.debug(f"  Speaker {speaker_label} averaged {embeddings_array.shape[0]} windows")
    else:
        # Already single embedding
        embedding_np = embeddings_array.squeeze()
    
    logger.debug(f"  Speaker {speaker_label} before norm - first 5: {embedding_np[:5]}")
    logger.debug(f"  Speaker {speaker_label} before norm - norm: {np.linalg.norm(embedding_np):.6f}")
    
    embedding_np = embedding_np / np.linalg.norm(embedding_np)
    logger.debug(f"  Speaker {speaker_label} after norm - first 5: {embedding_np[:5]}")
    
    return embedding_np


def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
    
    Returns:
        Similarity score between -1 and 1 (higher = more similar)
    """
    # Both should already be normalized, but ensure it
    emb1_norm = embedding1 / np.linalg.norm(embedding1)
    emb2_norm = embedding2 / np.linalg.norm(embedding2)
    
    similarity = np.dot(emb1_norm, emb2_norm)
    
    return float(similarity)


def extract_embeddings_per_speaker(
    audio_path: Path,
    words_with_speakers: list,
    min_duration_ms: int = 2000
) -> Dict[str, np.ndarray]:
    """
    Extract one embedding per speaker from diarized words.
    
    For each speaker, finds the longest continuous segment and extracts embedding.
    
    Args:
        audio_path: Path to audio file
        words_with_speakers: List of words with speaker labels and timestamps
        min_duration_ms: Minimum duration to consider for embedding
    
    Returns:
        Dictionary mapping speaker labels to embeddings
    """
    logger.info(f"Extracting embeddings per speaker from {audio_path}")
    
    # Group words by speaker
    speaker_segments: Dict[str, list] = {}
    
    for word in words_with_speakers:
        speaker = word.get("speaker")
        if speaker not in speaker_segments:
            speaker_segments[speaker] = []
        speaker_segments[speaker].append(word)
    
    # For each speaker, find longest continuous segment
    speaker_embeddings = {}
    
    for speaker, words in speaker_segments.items():
        if not words:
            continue
        
        # Find longest continuous segment (words close together)
        current_segment_start = words[0]["start"]
        current_segment_end = words[0]["end"]
        longest_segment = (current_segment_start, current_segment_end)
        longest_duration = current_segment_end - current_segment_start
        
        for i in range(1, len(words)):
            gap = words[i]["start"] - current_segment_end
            
            if gap < 1000:  # Less than 1 second gap
                current_segment_end = words[i]["end"]
            else:
                # Check if current segment is longest
                duration = current_segment_end - current_segment_start
                if duration > longest_duration:
                    longest_segment = (current_segment_start, current_segment_end)
                    longest_duration = duration
                
                # Start new segment
                current_segment_start = words[i]["start"]
                current_segment_end = words[i]["end"]
        
        # Check final segment
        duration = current_segment_end - current_segment_start
        if duration > longest_duration:
            longest_segment = (current_segment_start, current_segment_end)
            longest_duration = duration
        
        # Extract embedding from longest segment if long enough
        if longest_duration >= min_duration_ms:
            start_ms, end_ms = longest_segment
            embedding = extract_embedding_from_segment(audio_path, start_ms, end_ms, speaker_label=speaker)
            speaker_embeddings[speaker] = embedding
            logger.info(f"  {speaker}: extracted from {longest_duration}ms segment [{start_ms}-{end_ms}ms]")
        else:
            logger.warning(f"  {speaker}: longest segment only {longest_duration}ms (< {min_duration_ms}ms), skipping")
    
    return speaker_embeddings


def match_speaker_to_enrollment(
    enrollment_embedding: np.ndarray,
    speaker_embeddings: Dict[str, np.ndarray],
    threshold: float = 0.65
) -> Optional[str]:
    """
    Find which speaker (if any) matches the enrollment.
    
    Args:
        enrollment_embedding: Embedding from enrollment audio
        speaker_embeddings: Dictionary of speaker labels to embeddings
        threshold: Minimum similarity to consider a match
    
    Returns:
        Speaker label that matches, or None if no match
    """
    best_match = None
    best_score = threshold
    
    logger.info("=" * 60)
    logger.info("SPEAKER MATCHING DEBUG:")
    logger.info(f"Enrollment embedding shape: {enrollment_embedding.shape}")
    logger.info(f"Number of speakers in chunk: {len(speaker_embeddings)}")
    logger.info(f"Threshold: {threshold}")
    logger.info("-" * 60)
    
    similarities = {}
    for speaker, embedding in speaker_embeddings.items():
        similarity = cosine_similarity(enrollment_embedding, embedding)
        similarities[speaker] = similarity
        logger.info(f"  Speaker {speaker}:")
        logger.info(f"    Embedding shape: {embedding.shape}")
        logger.info(f"    Cosine similarity: {similarity:.4f}")
        logger.info(f"    Above threshold? {similarity > threshold}")
        
        if similarity > best_score:
            best_score = similarity
            best_match = speaker
    
    logger.info("-" * 60)
    if best_match:
        logger.info(f"✓ MATCHED: Speaker {best_match} with similarity {best_score:.4f}")
    else:
        logger.warning(f"✗ NO MATCH: Best similarity was {max(similarities.values()):.4f}, threshold is {threshold}")
        logger.warning(f"   Speakers: {list(similarities.keys())}")
        logger.warning(f"   Scores: {[f'{s:.4f}' for s in similarities.values()]}")
    logger.info("=" * 60)
    
    return best_match

