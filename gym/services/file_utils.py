import logging
import uuid
import os
from typing import Optional
from django.core.files.uploadedfile import UploadedFile
from .image_utils import optimize_image
from .s3_service import S3Service

logger = logging.getLogger(__name__)


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """Generate unique filename with UUID"""
    name, ext = os.path.splitext(original_filename)
    unique_id = str(uuid.uuid4())
    return f"{prefix}{unique_id}{ext}" if prefix else f"{unique_id}{ext}"


def upload_file_to_s3(file: UploadedFile, folder: str = "uploads") -> Optional[str]:
    """Optimiza imágenes y las sube a S3. Devuelve la URL."""
    if _is_image(file):
        try:
            file = optimize_image(file, folder=folder)
        except Exception:
            logger.exception('No se pudo optimizar la imagen; se sube el original')
            file.seek(0)

    s3_service = S3Service()
    filename = generate_unique_filename(file.name, f"{folder}/")
    return s3_service.upload_file(
        file_obj=file,
        key=filename,
        content_type=file.content_type
    )


def _is_image(file: UploadedFile) -> bool:
    content_type = (file.content_type or '').lower()
    return content_type.startswith('image/')


def delete_file_from_s3(file_url: str) -> bool:
    """Delete file from S3 using URL"""
    s3_service = S3Service()
    
    # Extract key from URL
    if file_url:
        # Handle both custom domain and S3 URLs
        if s3_service.bucket_name in file_url:
            key = file_url.split(f"{s3_service.bucket_name}/")[-1]
        else:
            key = file_url.split("/")[-1]
        
        return s3_service.delete_file(key)
    
    return False