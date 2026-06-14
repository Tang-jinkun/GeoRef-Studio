from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.image_file import ImageFileRead
from app.services.image_service import save_uploaded_image

router = APIRouter(prefix="/image")


@router.post("/upload", response_model=ApiResponse[ImageFileRead])
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ApiResponse[ImageFileRead]:
    image_file = await save_uploaded_image(db, file)
    return ApiResponse(data=ImageFileRead.model_validate(image_file))

