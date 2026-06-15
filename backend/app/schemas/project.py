from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from app.schemas.image_file import ImageFileRead


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    image_id: UUID

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Project name is required")
        return name


class ProjectRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    image_id: UUID
    image_path: str
    status: str
    transform_matrix: list[list[float]] | None = None
    rms_error: float | None = None
    transform_type: str | None = None
    target_crs: str | None = None
    rms_meters: float | None = None
    georef_result_path: str | None = None
    georef_time: datetime | None = None
    create_time: datetime
    update_time: datetime
    image: ImageFileRead | None = None

    model_config = ConfigDict(from_attributes=True)
