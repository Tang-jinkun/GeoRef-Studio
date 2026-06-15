from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.control_point import ControlPoint
from app.models.project import Project
from app.schemas.control_point import ControlPointCreate
from app.schemas.control_point import ControlPointUpdate


def _get_project_or_404(db: Session, project_id: UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _invalidate_georef(project: Project) -> None:
    if project.georef_result_path:
        result_path = Path(project.georef_result_path)
        result_path.unlink(missing_ok=True)
        result_path.with_name("georef_preview.png").unlink(missing_ok=True)
    project.status = "未配准"
    project.transform_matrix = None
    project.rms_error = None
    project.transform_type = None
    project.target_crs = None
    project.rms_meters = None
    project.georef_result_path = None
    project.georef_time = None


def create_control_point(db: Session, payload: ControlPointCreate) -> ControlPoint:
    project = _get_project_or_404(db, payload.project_id)
    control_point = ControlPoint(**payload.model_dump())
    _invalidate_georef(project)
    db.add(control_point)
    db.commit()
    db.refresh(control_point)
    return control_point


def list_control_points(db: Session, project_id: UUID) -> list[ControlPoint]:
    _get_project_or_404(db, project_id)
    statement = (
        select(ControlPoint)
        .where(ControlPoint.project_id == project_id)
        .order_by(ControlPoint.create_time.asc(), ControlPoint.id.asc())
    )
    return list(db.scalars(statement).all())


def get_control_point(db: Session, control_point_id: UUID) -> ControlPoint:
    control_point = db.get(ControlPoint, control_point_id)
    if control_point is None:
        raise HTTPException(status_code=404, detail="Control point not found")
    return control_point


def update_control_point(
    db: Session,
    control_point_id: UUID,
    payload: ControlPointUpdate,
) -> ControlPoint:
    control_point = get_control_point(db, control_point_id)
    project = _get_project_or_404(db, control_point.project_id)
    changes = payload.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(control_point, field, value)

    control_point.residual = None
    control_point.delta_x = None
    control_point.delta_y = None
    _invalidate_georef(project)
    db.commit()
    db.refresh(control_point)
    return control_point


def delete_control_point(db: Session, control_point_id: UUID) -> None:
    control_point = get_control_point(db, control_point_id)
    project = _get_project_or_404(db, control_point.project_id)
    _invalidate_georef(project)
    db.delete(control_point)
    db.commit()
