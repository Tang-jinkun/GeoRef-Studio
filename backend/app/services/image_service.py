from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from fastapi import UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.image_file import ImageFile

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "tif", "tiff", "bmp"}
MAX_UPLOAD_BYTES = 500 * 1024 * 1024


def _uploads_dir() -> Path:
    path = Path(settings.storage_root).resolve() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _validate_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported image format")
    return "jpg" if suffix == "jpeg" else suffix


async def save_uploaded_image(db: Session, file: UploadFile) -> ImageFile:
    original_name = file.filename or "upload"
    extension = _validate_extension(original_name)
    stored_name = f"{uuid4()}.{extension}"
    storage_path = _uploads_dir() / stored_name

    size_bytes = 0
    with storage_path.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            size_bytes += len(chunk)
            if size_bytes > MAX_UPLOAD_BYTES:
                storage_path.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="Image exceeds 500MB limit")
            output.write(chunk)

    try:
        with Image.open(storage_path) as image:
            width, height = image.size
            image_format = (image.format or extension).upper()
    except Exception as exc:
        storage_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Invalid image file") from exc

    image_file = ImageFile(
        original_name=original_name,
        storage_path=str(storage_path),
        width=width,
        height=height,
        size_bytes=size_bytes,
        format=image_format,
    )
    db.add(image_file)
    db.commit()
    db.refresh(image_file)
    return image_file

