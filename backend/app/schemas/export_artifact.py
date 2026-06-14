from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict


class GeoTiffExportRequest(BaseModel):
    project_id: UUID


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
