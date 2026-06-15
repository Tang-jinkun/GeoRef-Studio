import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
import rasterio
from affine import Affine
from PIL import Image
from pyproj import Transformer

WGS84_CRS = "EPSG:4326"
DEFAULT_TARGET_CRS = "EPSG:3857"
TRANSFORM_AUTO = "auto"
TRANSFORM_PROJECTIVE = "projective"
TRANSFORM_POLYNOMIAL_1 = "polynomial_1"
TRANSFORM_POLYNOMIAL_2 = "polynomial_2"
TRANSFORM_TPS = "tps"
SUPPORTED_TRANSFORMS = {
    TRANSFORM_AUTO,
    TRANSFORM_PROJECTIVE,
    TRANSFORM_POLYNOMIAL_1,
    TRANSFORM_POLYNOMIAL_2,
    TRANSFORM_TPS,
}
MIN_POINTS_BY_TRANSFORM = {
    TRANSFORM_PROJECTIVE: 4,
    TRANSFORM_POLYNOMIAL_1: 3,
    TRANSFORM_POLYNOMIAL_2: 6,
    TRANSFORM_TPS: 10,
}
MAX_SYNC_DIMENSION = 10_000
MAX_PREVIEW_DIMENSION = 4096


@dataclass(frozen=True)
class WarpPoint:
    pixel_x: float
    pixel_y: float
    longitude: float
    latitude: float


@dataclass(frozen=True)
class WarpResidual:
    predicted_longitude: float
    predicted_latitude: float
    delta_x: float
    delta_y: float
    residual_degrees: float
    delta_x_meters: float
    delta_y_meters: float
    residual_meters: float


@dataclass(frozen=True)
class WarpResult:
    transform_type: str
    target_crs: str
    transform_matrix: list[list[float]] | None
    residuals: list[WarpResidual]
    rms_degrees: float
    rms_meters: float
    output_path: Path


def resolve_transform_type(transform_type: str, point_count: int) -> str:
    if transform_type not in SUPPORTED_TRANSFORMS:
        raise ValueError(f"Unsupported transform type: {transform_type}")
    if transform_type != TRANSFORM_AUTO:
        return transform_type
    if point_count >= MIN_POINTS_BY_TRANSFORM[TRANSFORM_PROJECTIVE]:
        return TRANSFORM_PROJECTIVE
    return TRANSFORM_POLYNOMIAL_1


def minimum_points_for_transform(transform_type: str) -> int:
    if transform_type == TRANSFORM_AUTO:
        return MIN_POINTS_BY_TRANSFORM[TRANSFORM_POLYNOMIAL_1]
    return MIN_POINTS_BY_TRANSFORM[transform_type]


def warp_image_with_gcps(
    source_path: Path,
    output_path: Path,
    points: list[WarpPoint],
    transform_type: str = TRANSFORM_AUTO,
    target_crs: str = DEFAULT_TARGET_CRS,
) -> WarpResult:
    selected_transform = resolve_transform_type(transform_type, len(points))
    minimum_points = minimum_points_for_transform(selected_transform)
    if len(points) < minimum_points:
        raise ValueError(f"{selected_transform} requires at least {minimum_points} control points")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if selected_transform == TRANSFORM_PROJECTIVE:
        return _warp_projective(source_path, output_path, points, selected_transform, target_crs)
    return _warp_with_gdal(source_path, output_path, points, selected_transform, target_crs)


def geotiff_bounds_as_wgs84(path: Path) -> list[list[float]]:
    with rasterio.open(path) as dataset:
        bounds = dataset.bounds
        source_crs = dataset.crs.to_string() if dataset.crs else DEFAULT_TARGET_CRS
    transformer = Transformer.from_crs(source_crs, WGS84_CRS, always_xy=True)
    corners = [
        (bounds.left, bounds.top),
        (bounds.right, bounds.top),
        (bounds.right, bounds.bottom),
        (bounds.left, bounds.bottom),
    ]
    return [[float(x), float(y)] for x, y in (transformer.transform(x, y) for x, y in corners)]


def build_preview_png(geotiff_path: Path, preview_path: Path) -> None:
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(geotiff_path) as dataset:
        data = dataset.read()

    if data.shape[0] >= 4:
        array = np.moveaxis(data[:4], 0, -1)
        mode = "RGBA"
    elif data.shape[0] >= 3:
        array = np.moveaxis(data[:3], 0, -1)
        mode = "RGB"
    else:
        array = data[0]
        mode = "L"

    if array.dtype != np.uint8:
        array = _to_uint8(array)

    image = Image.fromarray(array, mode=mode)
    image.thumbnail((MAX_PREVIEW_DIMENSION, MAX_PREVIEW_DIMENSION), Image.Resampling.LANCZOS)
    image.save(preview_path)


def _warp_projective(
    source_path: Path,
    output_path: Path,
    points: list[WarpPoint],
    transform_type: str,
    target_crs: str,
) -> WarpResult:
    transformer = Transformer.from_crs(WGS84_CRS, target_crs, always_xy=True)
    inverse_transformer = Transformer.from_crs(target_crs, WGS84_CRS, always_xy=True)
    source_points = np.array([[point.pixel_x, point.pixel_y] for point in points], dtype=np.float64)
    target_points = np.array(
        [transformer.transform(point.longitude, point.latitude) for point in points],
        dtype=np.float64,
    )

    homography, _ = cv2.findHomography(source_points, target_points, method=0)
    if homography is None:
        raise ValueError("Projective transform could not be estimated")

    with rasterio.open(source_path) as source:
        source_data = source.read()
        source_height = source.height
        source_width = source.width

    corners = np.array(
        [[[0.0, 0.0], [source_width, 0.0], [source_width, source_height], [0.0, source_height]]],
        dtype=np.float64,
    )
    projected_corners = cv2.perspectiveTransform(corners, homography)[0]
    min_x = float(np.min(projected_corners[:, 0]))
    max_x = float(np.max(projected_corners[:, 0]))
    min_y = float(np.min(projected_corners[:, 1]))
    max_y = float(np.max(projected_corners[:, 1]))
    resolution = _estimate_resolution(source_points, target_points)
    output_width = max(1, int(math.ceil((max_x - min_x) / resolution)))
    output_height = max(1, int(math.ceil((max_y - min_y) / resolution)))
    scale_factor = max(output_width / MAX_SYNC_DIMENSION, output_height / MAX_SYNC_DIMENSION, 1.0)
    if scale_factor > 1.0:
        resolution *= scale_factor
        output_width = max(1, int(math.ceil((max_x - min_x) / resolution)))
        output_height = max(1, int(math.ceil((max_y - min_y) / resolution)))

    source_image = np.moveaxis(source_data, 0, -1)
    if source_image.shape[2] == 1:
        source_image = source_image[:, :, 0]

    map_to_output = np.array(
        [
            [1.0 / resolution, 0.0, -min_x / resolution],
            [0.0, -1.0 / resolution, max_y / resolution],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    source_to_output = map_to_output @ homography
    warped = cv2.warpPerspective(
        source_image,
        source_to_output,
        (output_width, output_height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )

    if source_data.shape[0] < 4:
        alpha_source = np.full((source_height, source_width), _dtype_max(source_data.dtype), dtype=source_data.dtype)
        alpha = cv2.warpPerspective(
            alpha_source,
            source_to_output,
            (output_width, output_height),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )
        if warped.ndim == 2:
            warped = np.stack([warped, alpha], axis=-1)
        else:
            warped = np.dstack([warped, alpha])

    if warped.ndim == 2:
        output_data = warped[np.newaxis, :, :]
    else:
        output_data = np.moveaxis(warped, -1, 0)

    profile = dict(
        driver="GTiff",
        height=output_height,
        width=output_width,
        count=output_data.shape[0],
        dtype=str(output_data.dtype),
        crs=target_crs,
        transform=Affine(resolution, 0.0, min_x, 0.0, -resolution, max_y),
        compress="deflate",
    )
    with rasterio.open(output_path, "w", **profile) as target:
        target.write(output_data)

    residuals = _projective_residuals(points, homography, target_crs)
    return _build_warp_result(transform_type, target_crs, homography.tolist(), residuals, output_path)


def _warp_with_gdal(
    source_path: Path,
    output_path: Path,
    points: list[WarpPoint],
    transform_type: str,
    target_crs: str,
) -> WarpResult:
    transformer = Transformer.from_crs(WGS84_CRS, target_crs, always_xy=True)
    run_id = uuid4().hex[:8]
    work_dir = output_path.parent / f"gdalwarp_{run_id}"
    work_dir.mkdir(parents=True, exist_ok=False)
    vrt_path = work_dir / "gcps.vrt"

    translate_command = [
        "gdal_translate",
        "-of",
        "VRT",
        "-a_srs",
        target_crs,
    ]
    target_points = []
    source_points = []
    for point in points:
        x, y = transformer.transform(point.longitude, point.latitude)
        translate_command.extend(["-gcp", str(point.pixel_x), str(point.pixel_y), str(x), str(y)])
        source_points.append([point.pixel_x, point.pixel_y])
        target_points.append([x, y])
    translate_command.extend([str(source_path), str(vrt_path)])

    warp_command = [
        "gdalwarp",
        "-overwrite",
        "-r",
        "bilinear",
        "-dstalpha",
        "-t_srs",
        target_crs,
    ]
    if transform_type == TRANSFORM_TPS:
        warp_command.append("-tps")
    elif transform_type == TRANSFORM_POLYNOMIAL_2:
        warp_command.extend(["-order", "2"])
    else:
        warp_command.extend(["-order", "1"])
    warp_command.extend([str(vrt_path), str(output_path)])

    try:
        subprocess.run(translate_command, check=True, capture_output=True, text=True)
        subprocess.run(warp_command, check=True, capture_output=True, text=True)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    residuals = _polynomial_residuals(
        points,
        np.array(source_points, dtype=np.float64),
        np.array(target_points, dtype=np.float64),
        target_crs,
        degree=2 if transform_type == TRANSFORM_POLYNOMIAL_2 else 1,
        force_exact=transform_type == TRANSFORM_TPS,
    )
    matrix = None
    if transform_type in {TRANSFORM_POLYNOMIAL_1, TRANSFORM_POLYNOMIAL_2}:
        matrix = _fit_polynomial(
            source_points,
            target_points,
            degree=2 if transform_type == TRANSFORM_POLYNOMIAL_2 else 1,
        ).tolist()
    return _build_warp_result(transform_type, target_crs, matrix, residuals, output_path)


def _build_warp_result(
    transform_type: str,
    target_crs: str,
    matrix: list[list[float]] | None,
    residuals: list[WarpResidual],
    output_path: Path,
) -> WarpResult:
    squared_degree_sum = sum(residual.residual_degrees**2 for residual in residuals)
    squared_meter_sum = sum(residual.residual_meters**2 for residual in residuals)
    count = max(len(residuals), 1)
    return WarpResult(
        transform_type=transform_type,
        target_crs=target_crs,
        transform_matrix=matrix,
        residuals=residuals,
        rms_degrees=float(math.sqrt(squared_degree_sum / count)),
        rms_meters=float(math.sqrt(squared_meter_sum / count)),
        output_path=output_path,
    )


def _projective_residuals(
    points: list[WarpPoint],
    homography: np.ndarray,
    target_crs: str,
) -> list[WarpResidual]:
    transformer = Transformer.from_crs(WGS84_CRS, target_crs, always_xy=True)
    inverse_transformer = Transformer.from_crs(target_crs, WGS84_CRS, always_xy=True)
    source_points = np.array([[[point.pixel_x, point.pixel_y]] for point in points], dtype=np.float64)
    predicted = cv2.perspectiveTransform(source_points, homography)[:, 0, :]
    return _build_residuals(points, predicted, transformer, inverse_transformer)


def _polynomial_residuals(
    points: list[WarpPoint],
    source_points: np.ndarray,
    target_points: np.ndarray,
    target_crs: str,
    degree: int,
    force_exact: bool = False,
) -> list[WarpResidual]:
    transformer = Transformer.from_crs(WGS84_CRS, target_crs, always_xy=True)
    inverse_transformer = Transformer.from_crs(target_crs, WGS84_CRS, always_xy=True)
    predicted = target_points if force_exact else _predict_polynomial(source_points, target_points, degree)
    return _build_residuals(points, predicted, transformer, inverse_transformer)


def _build_residuals(
    points: list[WarpPoint],
    predicted_target: np.ndarray,
    transformer: Transformer,
    inverse_transformer: Transformer,
) -> list[WarpResidual]:
    residuals = []
    for point, predicted in zip(points, predicted_target, strict=True):
        target_x, target_y = transformer.transform(point.longitude, point.latitude)
        delta_x_meters = float(predicted[0] - target_x)
        delta_y_meters = float(predicted[1] - target_y)
        residual_meters = float(math.hypot(delta_x_meters, delta_y_meters))
        predicted_longitude, predicted_latitude = inverse_transformer.transform(predicted[0], predicted[1])
        delta_x = float(predicted_longitude - point.longitude)
        delta_y = float(predicted_latitude - point.latitude)
        residuals.append(
            WarpResidual(
                predicted_longitude=float(predicted_longitude),
                predicted_latitude=float(predicted_latitude),
                delta_x=delta_x,
                delta_y=delta_y,
                residual_degrees=float(math.hypot(delta_x, delta_y)),
                delta_x_meters=delta_x_meters,
                delta_y_meters=delta_y_meters,
                residual_meters=residual_meters,
            )
        )
    return residuals


def _fit_polynomial(source_points: np.ndarray | list[list[float]], target_points: np.ndarray | list[list[float]], degree: int) -> np.ndarray:
    source = np.array(source_points, dtype=np.float64)
    target = np.array(target_points, dtype=np.float64)
    design = _polynomial_terms(source, degree)
    coef_x, *_ = np.linalg.lstsq(design, target[:, 0], rcond=None)
    coef_y, *_ = np.linalg.lstsq(design, target[:, 1], rcond=None)
    return np.vstack([coef_x, coef_y])


def _predict_polynomial(source_points: np.ndarray, target_points: np.ndarray, degree: int) -> np.ndarray:
    coefficients = _fit_polynomial(source_points, target_points, degree)
    design = _polynomial_terms(source_points, degree)
    return np.column_stack([design @ coefficients[0], design @ coefficients[1]])


def _polynomial_terms(source_points: np.ndarray, degree: int) -> np.ndarray:
    x = source_points[:, 0]
    y = source_points[:, 1]
    if degree == 1:
        return np.column_stack([x, y, np.ones_like(x)])
    if degree == 2:
        return np.column_stack([x, y, x * y, x * x, y * y, np.ones_like(x)])
    raise ValueError(f"Unsupported polynomial degree: {degree}")


def _estimate_resolution(source_points: np.ndarray, target_points: np.ndarray) -> float:
    resolutions = []
    for left_index in range(len(source_points)):
        for right_index in range(left_index + 1, len(source_points)):
            source_distance = np.linalg.norm(source_points[left_index] - source_points[right_index])
            target_distance = np.linalg.norm(target_points[left_index] - target_points[right_index])
            if source_distance > 0 and target_distance > 0:
                resolutions.append(target_distance / source_distance)
    if not resolutions:
        return 1.0
    return max(float(np.median(resolutions)), 0.01)


def _dtype_max(dtype: np.dtype) -> int | float:
    if np.issubdtype(dtype, np.integer):
        return int(np.iinfo(dtype).max)
    return 1.0


def _to_uint8(array: np.ndarray) -> np.ndarray:
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return np.zeros_like(array, dtype=np.uint8)
    lower = float(np.min(finite))
    upper = float(np.max(finite))
    if math.isclose(lower, upper):
        return np.zeros_like(array, dtype=np.uint8)
    scaled = (array.astype(np.float64) - lower) / (upper - lower) * 255.0
    return np.clip(scaled, 0, 255).astype(np.uint8)
