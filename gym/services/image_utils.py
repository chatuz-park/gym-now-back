import logging
import os
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

MAX_DIMENSIONS = {
    'profiles': 800,
    'exercises': 1600,
}
DEFAULT_MAX_DIMENSION = 1600
JPEG_QUALITY = 82


def optimize_image(file: UploadedFile, folder: str = 'uploads') -> InMemoryUploadedFile:
    """Reduce dimensiones y comprime la imagen antes de subirla a S3."""
    max_dimension = MAX_DIMENSIONS.get(folder, DEFAULT_MAX_DIMENSION)
    file.seek(0)

    with Image.open(file) as image:
        image = ImageOps.exif_transpose(image)
        image = _to_rgb(image)

        if image.width > max_dimension or image.height > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        buffer.seek(0)

    original_name = os.path.basename(getattr(file, 'name', 'image.jpg') or 'image.jpg')
    filename = f'{os.path.splitext(original_name)[0]}.jpg'
    return InMemoryUploadedFile(
        file=buffer,
        field_name=getattr(file, 'field_name', None),
        name=filename,
        content_type='image/jpeg',
        size=buffer.getbuffer().nbytes,
        charset=None,
    )


def _to_rgb(image: Image.Image) -> Image.Image:
    if image.mode in ('RGBA', 'LA', 'P'):
        rgba = image.convert('RGBA')
        background = Image.new('RGB', rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    if image.mode != 'RGB':
        return image.convert('RGB')
    return image
