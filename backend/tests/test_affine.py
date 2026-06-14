import math

import pytest

from app.gis.affine import AffinePoint
from app.gis.affine import fit_affine_transform


def test_fit_affine_transform_exact_points() -> None:
    points = [
        AffinePoint(pixel_x=0, pixel_y=0, longitude=100, latitude=20),
        AffinePoint(pixel_x=10, pixel_y=0, longitude=101, latitude=20),
        AffinePoint(pixel_x=0, pixel_y=10, longitude=100, latitude=21),
        AffinePoint(pixel_x=10, pixel_y=10, longitude=101, latitude=21),
    ]

    result = fit_affine_transform(points)

    assert result.matrix[0] == pytest.approx([0.1, 0.0, 100.0])
    assert result.matrix[1] == pytest.approx([0.0, 0.1, 20.0])
    assert result.rms == pytest.approx(0.0)
    assert all(residual.residual == pytest.approx(0.0) for residual in result.residuals)


def test_fit_affine_transform_with_overdetermined_points() -> None:
    points = [
        AffinePoint(pixel_x=0, pixel_y=0, longitude=10, latitude=30),
        AffinePoint(pixel_x=100, pixel_y=0, longitude=11, latitude=30),
        AffinePoint(pixel_x=0, pixel_y=100, longitude=10, latitude=31),
        AffinePoint(pixel_x=100, pixel_y=100, longitude=11.01, latitude=31.02),
    ]

    result = fit_affine_transform(points)

    assert len(result.residuals) == 4
    assert result.rms > 0
    assert math.isfinite(result.rms)


def test_fit_affine_transform_requires_three_points() -> None:
    points = [
        AffinePoint(pixel_x=0, pixel_y=0, longitude=100, latitude=20),
        AffinePoint(pixel_x=10, pixel_y=0, longitude=101, latitude=20),
    ]

    with pytest.raises(ValueError, match="At least 3 control points"):
        fit_affine_transform(points)
