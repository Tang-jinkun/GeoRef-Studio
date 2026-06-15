from datetime import datetime
from datetime import timezone
import math
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from fastapi.responses import FileResponse
from pyproj import Transformer
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.gis.warp import DEFAULT_TARGET_CRS
from app.gis.warp import MIN_POINTS_BY_TRANSFORM
from app.gis.warp import TRANSFORM_AUTO
from app.gis.warp import TRANSFORM_POLYNOMIAL_1
from app.gis.warp import TRANSFORM_POLYNOMIAL_2
from app.gis.warp import TRANSFORM_PROJECTIVE
from app.gis.warp import TRANSFORM_TPS
from app.gis.warp import WGS84_CRS
from app.gis.warp import WarpPoint
from app.gis.warp import build_preview_png
from app.gis.warp import geotiff_bounds_as_wgs84
from app.gis.warp import minimum_points_for_transform
from app.gis.warp import resolve_transform_type
from app.gis.warp import warp_image_with_gcps
from app.models.control_point import ControlPoint
from app.models.project import Project

MIN_CONTROL_POINT_COUNT = 3
TRANSFORM_OPTIONS = [
    (TRANSFORM_AUTO, "自动"),
    (TRANSFORM_PROJECTIVE, "透视 Projective"),
    (TRANSFORM_POLYNOMIAL_1, "多项式 1"),
    (TRANSFORM_POLYNOMIAL_2, "多项式 2"),
    (TRANSFORM_TPS, "TPS 薄板样条"),
]


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


def _outputs_dir(project_id: UUID) -> Path:
    path = Path(settings.storage_root).resolve() / "outputs" / str(project_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _georef_result_path(project_id: UUID) -> Path:
    return _outputs_dir(project_id) / "georef_current.tif"


def _preview_png_path(project_id: UUID) -> Path:
    return _outputs_dir(project_id) / "georef_preview.png"


def run_georef(
    db: Session,
    project_id: UUID,
    transform_type: str = TRANSFORM_AUTO,
    target_crs: str = DEFAULT_TARGET_CRS,
) -> tuple[Project, list[ControlPoint], float | None]:
    project = _get_project_or_404(db, project_id)
    control_points = _list_project_control_points(db, project.id)
    enabled_points = [point for point in control_points if point.enabled]
    selected_transform = _resolve_requested_transform(transform_type, len(enabled_points))

    minimum_points = minimum_points_for_transform(selected_transform)
    if len(enabled_points) < minimum_points:
        raise HTTPException(
            status_code=400,
            detail=f"{selected_transform} requires at least {minimum_points} enabled control points",
        )

    source_path = Path(project.image_path)
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Source image file not found")

    warp_points = [
        WarpPoint(
            pixel_x=point.pixel_x,
            pixel_y=point.pixel_y,
            longitude=point.longitude,
            latitude=point.latitude,
        )
        for point in enabled_points
    ]
    output_path = _georef_result_path(project.id)
    preview_path = _preview_png_path(project.id)
    output_path.unlink(missing_ok=True)
    preview_path.unlink(missing_ok=True)

    try:
        result = warp_image_with_gcps(
            source_path,
            output_path,
            warp_points,
            selected_transform,
            target_crs,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Georeference warp failed") from exc

    for point in control_points:
        point.residual = None
        point.delta_x = None
        point.delta_y = None
        _clear_diagnostics(point)

    for point, residual in zip(enabled_points, result.residuals, strict=True):
        point.delta_x = residual.delta_x
        point.delta_y = residual.delta_y
        point.residual = residual.residual_degrees
        point.predicted_longitude = residual.predicted_longitude
        point.predicted_latitude = residual.predicted_latitude
        point.delta_x_meters = residual.delta_x_meters
        point.delta_y_meters = residual.delta_y_meters
        point.residual_meters = residual.residual_meters

    project.transform_matrix = result.transform_matrix
    project.rms_error = result.rms_degrees
    project.transform_type = result.transform_type
    project.target_crs = result.target_crs
    project.rms_meters = result.rms_meters
    project.georef_result_path = str(result.output_path)
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


def list_transform_options() -> list[dict[str, int | str]]:
    return [
        {
            "value": value,
            "label": label,
            "minimum_control_points": MIN_POINTS_BY_TRANSFORM.get(
                value,
                MIN_POINTS_BY_TRANSFORM[TRANSFORM_POLYNOMIAL_1],
            ),
        }
        for value, label in TRANSFORM_OPTIONS
    ]


def _resolve_requested_transform(transform_type: str, point_count: int) -> str:
    try:
        return resolve_transform_type(transform_type, point_count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
    if not project.transform_matrix or not project.transform_type or not project.target_crs:
        for point in control_points:
            _clear_diagnostics(point)
        return project.rms_meters

    transformer = Transformer.from_crs(WGS84_CRS, project.target_crs, always_xy=True)
    inverse_transformer = Transformer.from_crs(project.target_crs, WGS84_CRS, always_xy=True)
    squared_sum = 0.0
    measured_count = 0
    for point in control_points:
        if not point.enabled:
            _clear_diagnostics(point)
            continue

        predicted_target = _predict_target_coordinate(project, point.pixel_x, point.pixel_y)
        if predicted_target is None:
            _clear_diagnostics(point)
            continue

        target_x, target_y = transformer.transform(point.longitude, point.latitude)
        delta_x_meters = predicted_target[0] - target_x
        delta_y_meters = predicted_target[1] - target_y
        residual_meters = math.hypot(delta_x_meters, delta_y_meters)
        predicted_longitude, predicted_latitude = inverse_transformer.transform(
            predicted_target[0],
            predicted_target[1],
        )
        delta_longitude = predicted_longitude - point.longitude
        delta_latitude = predicted_latitude - point.latitude

        point.predicted_longitude = predicted_longitude
        point.predicted_latitude = predicted_latitude
        point.delta_x_meters = delta_x_meters
        point.delta_y_meters = delta_y_meters
        point.residual_meters = residual_meters
        squared_sum += residual_meters * residual_meters
        measured_count += 1

    if measured_count == 0:
        return project.rms_meters
    return float(math.sqrt(squared_sum / measured_count))


def _predict_target_coordinate(
    project: Project,
    pixel_x: float,
    pixel_y: float,
) -> tuple[float, float] | None:
    matrix = project.transform_matrix
    if not matrix:
        return None
    if project.transform_type == TRANSFORM_PROJECTIVE and len(matrix) == 3:
        denominator = matrix[2][0] * pixel_x + matrix[2][1] * pixel_y + matrix[2][2]
        if math.isclose(denominator, 0.0):
            return None
        target_x = (matrix[0][0] * pixel_x + matrix[0][1] * pixel_y + matrix[0][2]) / denominator
        target_y = (matrix[1][0] * pixel_x + matrix[1][1] * pixel_y + matrix[1][2]) / denominator
        return float(target_x), float(target_y)
    if project.transform_type == TRANSFORM_POLYNOMIAL_1 and len(matrix) == 2:
        terms = [pixel_x, pixel_y, 1.0]
        return _apply_polynomial_matrix(matrix, terms)
    if project.transform_type == TRANSFORM_POLYNOMIAL_2 and len(matrix) == 2:
        terms = [pixel_x, pixel_y, pixel_x * pixel_y, pixel_x * pixel_x, pixel_y * pixel_y, 1.0]
        return _apply_polynomial_matrix(matrix, terms)
    return None


def _apply_polynomial_matrix(matrix: list[list[float]], terms: list[float]) -> tuple[float, float] | None:
    if any(len(row) != len(terms) for row in matrix):
        return None
    target_x = sum(coefficient * term for coefficient, term in zip(matrix[0], terms, strict=True))
    target_y = sum(coefficient * term for coefficient, term in zip(matrix[1], terms, strict=True))
    return float(target_x), float(target_y)


def get_preview(db: Session, project_id: UUID) -> tuple[Project, list[list[float]]]:
    project = _get_project_or_404(db, project_id)
    if not project.georef_result_path:
        raise HTTPException(status_code=400, detail="Project is not georeferenced")
    if project.image is None:
        raise HTTPException(status_code=404, detail="Project image not found")

    geotiff_path = Path(project.georef_result_path)
    if not geotiff_path.exists():
        raise HTTPException(status_code=404, detail="Georeferenced raster not found")

    preview_path = _preview_png_path(project.id)
    if not preview_path.exists() or preview_path.stat().st_mtime < geotiff_path.stat().st_mtime:
        build_preview_png(geotiff_path, preview_path)

    coordinates = geotiff_bounds_as_wgs84(geotiff_path)
    return project, coordinates


def get_preview_image_response(db: Session, project_id: UUID) -> FileResponse:
    project, _ = get_preview(db, project_id)
    preview_path = _preview_png_path(project.id)
    return FileResponse(preview_path, filename=preview_path.name, media_type="image/png")
