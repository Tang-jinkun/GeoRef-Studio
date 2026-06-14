import pytest

from app.gis.geotiff import affine_matrix_to_transform


def test_affine_matrix_to_transform() -> None:
    transform = affine_matrix_to_transform([[0.1, 0.0, 100.0], [0.0, -0.1, 30.0]])

    assert transform.a == pytest.approx(0.1)
    assert transform.b == pytest.approx(0.0)
    assert transform.c == pytest.approx(100.0)
    assert transform.d == pytest.approx(0.0)
    assert transform.e == pytest.approx(-0.1)
    assert transform.f == pytest.approx(30.0)


def test_affine_matrix_to_transform_rejects_invalid_matrix() -> None:
    with pytest.raises(ValueError, match="2x3"):
        affine_matrix_to_transform([[1.0, 0.0], [0.0, 1.0]])
