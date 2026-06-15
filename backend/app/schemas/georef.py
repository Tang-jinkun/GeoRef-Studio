from uuid import UUID

from pydantic import BaseModel
from pydantic import Field

from app.schemas.control_point import ControlPointRead


class GeorefRunRequest(BaseModel):
    project_id: UUID
    transform_type: str = "auto"
    target_crs: str = "EPSG:3857"


class GeorefRunResult(BaseModel):
    project_id: UUID
    transform_matrix: list[list[float]]
    transform_type: str
    target_crs: str
    rms: float
    rms_meters: float | None = None
    fit_rms_meters: float | None = None
    check_rms_meters: float | None = None
    preview_available: bool = False
    control_points: list[ControlPointRead]


class RmsResult(BaseModel):
    project_id: UUID
    rms: float | None
    rms_meters: float | None = None
    fit_rms_meters: float | None = None
    check_rms_meters: float | None = None
    transform_type: str | None = None
    target_crs: str | None = None
    enabled_control_point_count: int
    minimum_required_count: int = 3
    control_points: list[ControlPointRead]


class GeorefPreviewResult(BaseModel):
    project_id: UUID
    image_id: UUID
    image_url: str
    coordinates: list[list[float]]
    opacity: float = 0.65


class TransformOption(BaseModel):
    value: str
    label: str
    minimum_control_points: int = Field(ge=3)
