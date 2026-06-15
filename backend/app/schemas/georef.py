from uuid import UUID

from pydantic import BaseModel

from app.schemas.control_point import ControlPointRead


class GeorefRunRequest(BaseModel):
    project_id: UUID


class GeorefRunResult(BaseModel):
    project_id: UUID
    transform_matrix: list[list[float]]
    rms: float
    rms_meters: float | None = None
    control_points: list[ControlPointRead]


class RmsResult(BaseModel):
    project_id: UUID
    rms: float | None
    rms_meters: float | None = None
    enabled_control_point_count: int
    minimum_required_count: int = 3
    control_points: list[ControlPointRead]


class GeorefPreviewResult(BaseModel):
    project_id: UUID
    image_id: UUID
    image_url: str
    coordinates: list[list[float]]
    opacity: float = 0.65
