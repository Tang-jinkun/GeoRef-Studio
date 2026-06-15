from datetime import datetime
from datetime import timezone
import math
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.gis.affine import AffinePoint
from app.gis.affine import fit_affine_transform
from app.models.control_point import ControlPoint
from app.models.project import Project

MIN_CONTROL_POINT_COUNT = 3


def _get_project_or_404(db: Session, project_id: UUID) -> Project:
    project = db.scalars(
        select(Project).options(joinedload(Project.image)).where(Project.id == project_id)
    ).first()
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


def run_georef(
    db: Session,
    project_id: UUID,
) -> tuple[Project, list[ControlPoint], float | None]:
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
    rms_meters = enrich_control_point_diagnostics(project, control_points)
    return project, control_points, rms_meters


def get_rms(
    db: Session,
    project_id: UUID,
) -> tuple[Project, list[ControlPoint], int, float | None]:
    project = _get_project_or_404(db, project_id)
    control_points = _list_project_control_points(db, project.id)
    enabled_count = len([point for point in control_points if point.enabled])
    rms_meters = enrich_control_point_diagnostics(project, control_points)
    return project, control_points, enabled_count, rms_meters


def _transform_pixel(matrix: list[list[float]], pixel_x: float, pixel_y: float) -> list[float]:
    longitude = matrix[0][0] * pixel_x + matrix[0][1] * pixel_y + matrix[0][2]
    latitude = matrix[1][0] * pixel_x + matrix[1][1] * pixel_y + matrix[1][2]
    return [float(longitude), float(latitude)]


def _degree_delta_to_meters(
    delta_longitude: float,
    delta_latitude: float,
    latitude: float,
) -> tuple[float, float, float]:
    latitude_rad = math.radians(latitude)
    meters_per_degree_latitude = (
        111132.92
        - 559.82 * math.cos(2 * latitude_rad)
        + 1.175 * math.cos(4 * latitude_rad)
        - 0.0023 * math.cos(6 * latitude_rad)
    )
    meters_per_degree_longitude = (
        111412.84 * math.cos(latitude_rad)
        - 93.5 * math.cos(3 * latitude_rad)
        + 0.118 * math.cos(5 * latitude_rad)
    )
    delta_x_meters = delta_longitude * meters_per_degree_longitude
    delta_y_meters = delta_latitude * meters_per_degree_latitude
    residual_meters = math.hypot(delta_x_meters, delta_y_meters)
    return delta_x_meters, delta_y_meters, residual_meters


def _clear_diagnostics(point: ControlPoint) -> None:
    point.predicted_longitude = None
    point.predicted_latitude = None
    point.delta_x_meters = None
    point.delta_y_meters = None
    point.residual_meters = None


def enrich_control_point_diagnostics(
    project: Project,
    control_points: list[ControlPoint],
) -> float | None:
    if not project.transform_matrix:
        for point in control_points:
            _clear_diagnostics(point)
        return None

    squared_sum = 0.0
    measured_count = 0
    for point in control_points:
        if not point.enabled:
            _clear_diagnostics(point)
            continue

        predicted_longitude, predicted_latitude = _transform_pixel(
            project.transform_matrix,
            point.pixel_x,
            point.pixel_y,
        )
        delta_longitude = predicted_longitude - point.longitude
        delta_latitude = predicted_latitude - point.latitude
        delta_x_meters, delta_y_meters, residual_meters = _degree_delta_to_meters(
            delta_longitude,
            delta_latitude,
            point.latitude,
        )

        point.predicted_longitude = predicted_longitude
        point.predicted_latitude = predicted_latitude
        point.delta_x_meters = delta_x_meters
        point.delta_y_meters = delta_y_meters
        point.residual_meters = residual_meters
        squared_sum += residual_meters * residual_meters
        measured_count += 1

    if measured_count == 0:
        return None
    return float(math.sqrt(squared_sum / measured_count))


def get_preview(db: Session, project_id: UUID) -> tuple[Project, list[list[float]]]:
    project = _get_project_or_404(db, project_id)
    if not project.transform_matrix:
        raise HTTPException(status_code=400, detail="Project is not georeferenced")
    if project.image is None:
        raise HTTPException(status_code=404, detail="Project image not found")

    width = project.image.width
    height = project.image.height
    coordinates = [
        _transform_pixel(project.transform_matrix, 0, 0),
        _transform_pixel(project.transform_matrix, width, 0),
        _transform_pixel(project.transform_matrix, width, height),
        _transform_pixel(project.transform_matrix, 0, height),
    ]
    return project, coordinates
