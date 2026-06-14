from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.control_point import ControlPointRead
from app.schemas.georef import GeorefRunRequest
from app.schemas.georef import GeorefRunResult
from app.schemas.georef import GeorefPreviewResult
from app.schemas.georef import RmsResult
from app.services.georef_service import MIN_CONTROL_POINT_COUNT
from app.services.georef_service import get_preview
from app.services.georef_service import get_rms
from app.services.georef_service import run_georef

router = APIRouter(prefix="/georef")


@router.post("/run", response_model=ApiResponse[GeorefRunResult])
def run_georef_endpoint(
    payload: GeorefRunRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[GeorefRunResult]:
    project, control_points = run_georef(db, payload.project_id)
    return ApiResponse(
        data=GeorefRunResult(
            project_id=project.id,
            transform_matrix=project.transform_matrix or [],
            rms=project.rms_error or 0.0,
            control_points=[
                ControlPointRead.model_validate(point) for point in control_points
            ],
        )
    )


@router.get("/rms", response_model=ApiResponse[RmsResult])
def get_rms_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse[RmsResult]:
    project, control_points, enabled_count = get_rms(db, project_id)
    return ApiResponse(
        data=RmsResult(
            project_id=project.id,
            rms=project.rms_error,
            enabled_control_point_count=enabled_count,
            minimum_required_count=MIN_CONTROL_POINT_COUNT,
            control_points=[
                ControlPointRead.model_validate(point) for point in control_points
            ],
        )
    )


@router.get("/preview", response_model=ApiResponse[GeorefPreviewResult])
def get_preview_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse[GeorefPreviewResult]:
    project, coordinates = get_preview(db, project_id)
    return ApiResponse(
        data=GeorefPreviewResult(
            project_id=project.id,
            image_id=project.image_id,
            image_url=f"/api/image/{project.image_id}/file",
            coordinates=coordinates,
        )
    )
