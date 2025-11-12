"""
Cloud storage service for audio files.

Supports both local filesystem (development) and Cloudinary (production).
"""

from pathlib import Path
from typing import Optional, BinaryIO
import cloudinary
import cloudinary.uploader
from loguru import logger
from app.config import settings
import os


# Initialize Cloudinary if enabled
if settings.USE_CLOUDINARY:
    if not all([settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET]):
        logger.warning("Cloudinary credentials incomplete - using local storage as fallback")
        settings.USE_CLOUDINARY = False
    else:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
        logger.info(f"Cloudinary initialized: {settings.CLOUDINARY_CLOUD_NAME}")


def upload_audio_file(file_path: Path, public_id: Optional[str] = None) -> str:
    """
    Upload an audio file to storage.
    
    Args:
        file_path: Local path to audio file
        public_id: Optional custom ID for the file
    
    Returns:
        URL or path to access the file
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if settings.USE_CLOUDINARY:
        return _upload_to_cloudinary(file_path, public_id)
    else:
        # For local storage, just return the relative path
        return str(file_path.relative_to(settings.STORAGE_ROOT))


def _upload_to_cloudinary(file_path: Path, public_id: Optional[str] = None) -> str:
    """
    Upload file to Cloudinary.
    
    Returns:
        Cloudinary secure URL
    """
    try:
        # Generate public_id if not provided
        if not public_id:
            public_id = file_path.stem
        
        # Add folder prefix
        full_public_id = f"{settings.CLOUDINARY_FOLDER}/{public_id}"
        
        logger.info(f"Uploading {file_path} to Cloudinary as {full_public_id}")
        
        # Upload with raw resource type for audio files
        result = cloudinary.uploader.upload(
            str(file_path),
            public_id=full_public_id,
            resource_type="raw",  # Use 'raw' for audio files
            overwrite=True,
            unique_filename=False
        )
        
        url = result.get("secure_url")
        logger.info(f"Uploaded successfully: {url}")
        
        return url
        
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise


def download_audio_file(url_or_path: str) -> Path:
    """
    Download or get local path for an audio file.
    
    Args:
        url_or_path: Cloudinary URL or local path
    
    Returns:
        Local path to the file
    """
    if settings.USE_CLOUDINARY and url_or_path.startswith("http"):
        return _download_from_cloudinary(url_or_path)
    else:
        # Local storage - return path
        return Path(settings.STORAGE_ROOT) / url_or_path


def _download_from_cloudinary(url: str) -> Path:
    """
    Download file from Cloudinary to temporary location.
    
    Returns:
        Local path to downloaded file
    """
    import httpx
    from urllib.parse import urlparse
    
    try:
        # Create temp directory
        temp_dir = Path(settings.STORAGE_ROOT) / "temp" / "downloads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract filename from URL
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        local_path = temp_dir / filename
        
        # Download if not already cached
        if not local_path.exists():
            logger.info(f"Downloading from Cloudinary: {url}")
            response = httpx.get(url)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded to: {local_path}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Failed to download from Cloudinary: {e}")
        raise


def delete_audio_file(url_or_path: str) -> bool:
    """
    Delete an audio file from storage.
    
    Args:
        url_or_path: Cloudinary URL or local path
    
    Returns:
        True if deleted successfully
    """
    if settings.USE_CLOUDINARY and url_or_path.startswith("http"):
        return _delete_from_cloudinary(url_or_path)
    else:
        # Local storage
        try:
            path = Path(settings.STORAGE_ROOT) / url_or_path
            if path.exists():
                path.unlink()
                logger.info(f"Deleted local file: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete local file: {e}")
            return False


def _delete_from_cloudinary(url: str) -> bool:
    """
    Delete file from Cloudinary.
    
    Returns:
        True if deleted successfully
    """
    try:
        # Extract public_id from URL
        # URL format: https://res.cloudinary.com/{cloud_name}/raw/upload/{folder}/{public_id}.ext
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        
        # Find the public_id (after 'upload/')
        upload_index = path_parts.index('upload')
        public_id_parts = path_parts[upload_index + 1:]
        public_id = '/'.join(public_id_parts)
        
        # Remove file extension
        public_id = os.path.splitext(public_id)[0]
        
        logger.info(f"Deleting from Cloudinary: {public_id}")
        
        result = cloudinary.uploader.destroy(public_id, resource_type="raw")
        
        if result.get("result") == "ok":
            logger.info(f"Deleted successfully: {public_id}")
            return True
        else:
            logger.warning(f"Delete result: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to delete from Cloudinary: {e}")
        return False

