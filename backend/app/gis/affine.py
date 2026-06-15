from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AffinePoint:
    pixel_x: float
    pixel_y: float
    longitude: float
    latitude: float


@dataclass(frozen=True)
class AffineResidual:
    predicted_longitude: float
    predicted_latitude: float
    delta_x: float
    delta_y: float
    residual: float


@dataclass(frozen=True)
class AffineResult:
    matrix: list[list[float]]
    residuals: list[AffineResidual]
    rms: float


def fit_affine_transform(points: list[AffinePoint]) -> AffineResult:
    if len(points) < 3:
        raise ValueError("At least 3 control points are required")

    source = np.array([[point.pixel_x, point.pixel_y, 1.0] for point in points], dtype=float)
    target_x = np.array([point.longitude for point in points], dtype=float)
    target_y = np.array([point.latitude for point in points], dtype=float)

    coef_x, *_ = np.linalg.lstsq(source, target_x, rcond=None)
    coef_y, *_ = np.linalg.lstsq(source, target_y, rcond=None)

    predicted_x = source @ coef_x
    predicted_y = source @ coef_y

    residuals = []
    squared_sum = 0.0
    for index, point in enumerate(points):
        delta_x = float(predicted_x[index] - point.longitude)
        delta_y = float(predicted_y[index] - point.latitude)
        residual = float(np.hypot(delta_x, delta_y))
        squared_sum += residual * residual
        residuals.append(
            AffineResidual(
                predicted_longitude=float(predicted_x[index]),
                predicted_latitude=float(predicted_y[index]),
                delta_x=delta_x,
                delta_y=delta_y,
                residual=residual,
            )
        )

    return AffineResult(
        matrix=[
            [float(coef_x[0]), float(coef_x[1]), float(coef_x[2])],
            [float(coef_y[0]), float(coef_y[1]), float(coef_y[2])],
        ],
        residuals=residuals,
        rms=float(np.sqrt(squared_sum / len(points))),
    )
