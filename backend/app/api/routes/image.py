import mimetypes
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.image_file import ImageFileRead
from app.services.image_service import get_image_file
from app.services.image_service import get_image_file_path
from app.services.image_service import save_uploaded_image

router = APIRouter(prefix="/image")


@router.post("/upload", response_model=ApiResponse[ImageFileRead])
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ApiResponse[ImageFileRead]:
    image_file = await save_uploaded_image(db, file)
    return ApiResponse(data=ImageFileRead.model_validate(image_file))


@router.get("/{image_id}/file")
def download_image_file(
    image_id: UUID,
    db: Session = Depends(get_db),
) -> FileResponse:
    image_file = get_image_file(db, image_id)
    path = get_image_file_path(db, image_id)
    media_type = mimetypes.guess_type(image_file.original_name)[0] or "application/octet-stream"
    return FileResponse(path, filename=image_file.original_name, media_type=media_type)
