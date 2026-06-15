from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ControlPointCreate(BaseModel):
    project_id: UUID
    pixel_x: float
    pixel_y: float
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    enabled: bool = True


class ControlPointUpdate(BaseModel):
    pixel_x: float | None = None
    pixel_y: float | None = None
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    enabled: bool | None = None


class ControlPointRead(BaseModel):
    id: UUID
    project_id: UUID
    pixel_x: float
    pixel_y: float
    longitude: float
    latitude: float
    residual: float | None = None
    delta_x: float | None = None
    delta_y: float | None = None
    predicted_longitude: float | None = None
    predicted_latitude: float | None = None
    delta_x_meters: float | None = None
    delta_y_meters: float | None = None
    residual_meters: float | None = None
    enabled: bool
    create_time: datetime
    update_time: datetime

    model_config = ConfigDict(from_attributes=True)
