from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.control_point import ControlPointRead
from app.schemas.georef import GeorefRunRequest
from app.schemas.georef import GeorefRunResult
from app.schemas.georef import GeorefPreviewResult
from app.schemas.georef import RmsResult
from app.schemas.georef import TransformOption
from app.services.georef_service import MIN_CONTROL_POINT_COUNT
from app.services.georef_service import get_preview
from app.services.georef_service import get_preview_image_response
from app.services.georef_service import get_rms
from app.services.georef_service import list_transform_options
from app.services.georef_service import run_georef

router = APIRouter(prefix="/georef")


@router.post("/run", response_model=ApiResponse[GeorefRunResult])
def run_georef_endpoint(
    payload: GeorefRunRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[GeorefRunResult]:
    project, control_points, rms_meters = run_georef(
        db,
        payload.project_id,
        payload.transform_type,
        payload.target_crs,
    )
    return ApiResponse(
        data=GeorefRunResult(
            project_id=project.id,
            transform_matrix=project.transform_matrix or [],
            transform_type=project.transform_type or payload.transform_type,
            target_crs=project.target_crs or payload.target_crs,
            rms=project.rms_error or 0.0,
            rms_meters=rms_meters,
            preview_available=bool(project.georef_result_path),
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
    project, control_points, enabled_count, rms_meters = get_rms(db, project_id)
    return ApiResponse(
        data=RmsResult(
            project_id=project.id,
            rms=project.rms_error,
            rms_meters=rms_meters,
            transform_type=project.transform_type,
            target_crs=project.target_crs,
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
            image_url=f"/api/georef/preview/{project.id}/image",
            coordinates=coordinates,
        )
    )


@router.get("/preview/{project_id}/image")
def get_preview_image_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
) -> FileResponse:
    return get_preview_image_response(db, project_id)


@router.get("/transform-options", response_model=ApiResponse[list[TransformOption]])
def list_transform_options_endpoint() -> ApiResponse[list[TransformOption]]:
    return ApiResponse(data=[TransformOption(**option) for option in list_transform_options()])
