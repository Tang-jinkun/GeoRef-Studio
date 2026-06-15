from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


class GeoTiffExportRequest(BaseModel):
    project_id: UUID


class XyzExportRequest(BaseModel):
    project_id: UUID
    min_zoom: int = Field(default=0, ge=0, le=22)
    max_zoom: int = Field(default=6, ge=0, le=22)

    @model_validator(mode="after")
    def validate_zoom_range(self) -> "XyzExportRequest":
        if self.max_zoom < self.min_zoom:
            raise ValueError("max_zoom must be greater than or equal to min_zoom")
        return self


class ExportArtifactRead(BaseModel):
    id: UUID
    project_id: UUID
    artifact_type: str
    file_name: str
    storage_path: str
    size_bytes: int
    status: str
    message: str | None = None
    create_time: datetime

    model_config = ConfigDict(from_attributes=True)
