from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.control_point import ControlPointCreate
from app.schemas.control_point import ControlPointRead
from app.schemas.control_point import ControlPointUpdate
from app.services.control_point_service import create_control_point
from app.services.control_point_service import delete_control_point
from app.services.control_point_service import get_control_point
from app.services.control_point_service import list_control_points
from app.services.control_point_service import update_control_point

router = APIRouter(prefix="/control-point")


@router.post("/create", response_model=ApiResponse[ControlPointRead])
def create_control_point_endpoint(
    payload: ControlPointCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[ControlPointRead]:
    control_point = create_control_point(db, payload)
    return ApiResponse(data=ControlPointRead.model_validate(control_point))


@router.get("/list", response_model=ApiResponse[list[ControlPointRead]])
def list_control_points_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse[list[ControlPointRead]]:
    control_points = list_control_points(db, project_id)
    return ApiResponse(
        data=[ControlPointRead.model_validate(point) for point in control_points]
    )


@router.get("/{control_point_id}", response_model=ApiResponse[ControlPointRead])
def get_control_point_endpoint(
    control_point_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse[ControlPointRead]:
    control_point = get_control_point(db, control_point_id)
    return ApiResponse(data=ControlPointRead.model_validate(control_point))


@router.patch("/{control_point_id}", response_model=ApiResponse[ControlPointRead])
def update_control_point_endpoint(
    control_point_id: UUID,
    payload: ControlPointUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[ControlPointRead]:
    control_point = update_control_point(db, control_point_id, payload)
    return ApiResponse(data=ControlPointRead.model_validate(control_point))


@router.delete("/{control_point_id}", response_model=ApiResponse[dict[str, bool]])
def delete_control_point_endpoint(
    control_point_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse[dict[str, bool]]:
    delete_control_point(db, control_point_id)
    return ApiResponse(data={"deleted": True})
