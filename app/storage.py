from pathlib import Path
from app.config import settings

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

