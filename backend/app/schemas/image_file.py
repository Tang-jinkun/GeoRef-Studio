from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict


class ImageFileRead(BaseModel):
    id: UUID
    original_name: str
    storage_path: str
    width: int
    height: int
    size_bytes: int
    format: str
    upload_time: datetime

    model_config = ConfigDict(from_attributes=True)

