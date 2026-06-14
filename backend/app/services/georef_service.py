from datetime import datetime
from datetime import timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.gis.affine import AffinePoint
from app.gis.affine import fit_affine_transform
from app.models.control_point import ControlPoint
from app.models.project import Project

MIN_CONTROL_POINT_COUNT = 3


def _get_project_or_404(db: Session, project_id: UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _list_project_control_points(db: Session, project_id: UUID) -> list[ControlPoint]:
    statement = (
        select(ControlPoint)
        .where(ControlPoint.project_id == project_id)
        .order_by(ControlPoint.create_time.asc(), ControlPoint.id.asc())
    )
    return list(db.scalars(statement).all())


def run_georef(db: Session, project_id: UUID) -> tuple[Project, list[ControlPoint]]:
    project = _get_project_or_404(db, project_id)
    control_points = _list_project_control_points(db, project.id)
    enabled_points = [point for point in control_points if point.enabled]

    if len(enabled_points) < MIN_CONTROL_POINT_COUNT:
        raise HTTPException(
            status_code=400,
            detail=f"At least {MIN_CONTROL_POINT_COUNT} enabled control points are required",
        )

    affine_points = [
        AffinePoint(
            pixel_x=point.pixel_x,
            pixel_y=point.pixel_y,
            longitude=point.longitude,
            latitude=point.latitude,
        )
        for point in enabled_points
    ]
    result = fit_affine_transform(affine_points)

    for point in control_points:
        point.residual = None
        point.delta_x = None
        point.delta_y = None

    for point, residual in zip(enabled_points, result.residuals, strict=True):
        point.delta_x = residual.delta_x
        point.delta_y = residual.delta_y
        point.residual = residual.residual

    project.transform_matrix = result.matrix
    project.rms_error = result.rms
    project.georef_time = datetime.now(timezone.utc)
    project.status = "已配准"
    db.commit()

    db.refresh(project)
    for point in control_points:
        db.refresh(point)
    return project, control_points


def get_rms(db: Session, project_id: UUID) -> tuple[Project, list[ControlPoint], int]:
    project = _get_project_or_404(db, project_id)
    control_points = _list_project_control_points(db, project.id)
    enabled_count = len([point for point in control_points if point.enabled])
    return project, control_points, enabled_count
