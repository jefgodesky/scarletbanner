import mimetypes
from io import BytesIO
from typing import Any

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage


def isstring(candidate: Any) -> bool:
    return isinstance(candidate, str) and len(candidate) > 0


def generate_test_image(filename: str = "test", format: str = "JPEG") -> SimpleUploadedFile:
    image = PILImage.new("RGB", (100, 100), color="red")
    byte_io = BytesIO()
    image.save(byte_io, format)
    byte_io.seek(0)
    filename = f"{filename}.{format.lower()}"
    content_type = mimetypes.guess_type(filename)[0] or f"image/{format.lower()}"
    return SimpleUploadedFile(filename, byte_io.read(), content_type)
