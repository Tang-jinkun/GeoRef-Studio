from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

CONTROL_POINT_ROLES = {"fit", "check"}


class ControlPointCreate(BaseModel):
    project_id: UUID
    pixel_x: float
    pixel_y: float
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    role: str = "fit"
    enabled: bool = True

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in CONTROL_POINT_ROLES:
            raise ValueError("Control point role must be fit or check")
        return value


class ControlPointUpdate(BaseModel):
    pixel_x: float | None = None
    pixel_y: float | None = None
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    role: str | None = None
    enabled: bool | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        if value is not None and value not in CONTROL_POINT_ROLES:
            raise ValueError("Control point role must be fit or check")
        return value


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
    role: str = "fit"
    enabled: bool
    create_time: datetime
    update_time: datetime

    model_config = ConfigDict(from_attributes=True)
