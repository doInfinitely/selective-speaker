from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/selective"
    ENV: str = "dev"
    STORAGE_ROOT: str = "./data"

    # Diarization mapper settings
    PAD_MS: int = 0  # No silence padding to avoid label drift
    ENROLL_DOMINANCE: float = 0.8
    SEGMENT_GAP_MS: int = 500
    SEGMENT_MIN_MS: int = 1000
    SEGMENT_MIN_CHARS: int = 6
    # Use majority speaker from chunk instead of enrollment label (fixes label drift)
    USE_MAJORITY_SPEAKER: bool = False  # Disabled - try without first

    # AssemblyAI settings
    ASSEMBLYAI_API_KEY: str = ""
    ASSEMBLYAI_WEBHOOK_SECRET: str = "devsecret"
    WEBHOOK_BASE_URL: str = "http://localhost:8000"  # For development; change in production
    
    # Audio settings
    AUDIO_SAMPLE_RATE: int = 16000  # 16kHz recommended for speech
    AUDIO_CHANNELS: int = 1  # Mono

    # Speaker embedding settings
    HUGGINGFACE_TOKEN: str = ""  # Required for pyannote models

    # Cloudinary settings (for production)
    USE_CLOUDINARY: bool = False  # Set to True in production
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_FOLDER: str = "selective-speaker"  # Folder name in Cloudinary

    class Config:
        env_file = ".env"


settings = Settings()

