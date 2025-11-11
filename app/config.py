from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/selective"
    ENV: str = "dev"
    STORAGE_ROOT: str = "./data"

    PAD_MS: int = 1000
    ENROLL_DOMINANCE: float = 0.8
    SEGMENT_GAP_MS: int = 500
    SEGMENT_MIN_MS: int = 1000
    SEGMENT_MIN_CHARS: int = 6

    ASSEMBLYAI_WEBHOOK_SECRET: str = "devsecret"

    class Config:
        env_file = ".env"


settings = Settings()

