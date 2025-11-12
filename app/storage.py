from pathlib import Path
from app.config import settings
from fastapi import UploadFile
import shutil

ROOT = Path(settings.STORAGE_ROOT)
ROOT.mkdir(parents=True, exist_ok=True)


def local_path(url_or_rel: str) -> Path:
    """
    For dev, treat audio_url as relative path under STORAGE_ROOT.
    In production, this would handle S3/GCS URLs differently.
    """
    p = ROOT / url_or_rel
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def save_uploaded_file(upload_file: UploadFile, filename: str) -> Path:
    """
    Save an uploaded file to storage.
    
    Args:
        upload_file: FastAPI UploadFile object
        filename: Desired filename
    
    Returns:
        Path where file was saved
    """
    file_path = ROOT / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    
    return file_path

