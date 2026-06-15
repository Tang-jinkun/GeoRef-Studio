import numpy as np
import pytest
import rasterio
from PIL import Image

from app.gis.warp import TRANSFORM_PROJECTIVE
from app.gis.warp import WarpPoint
from app.gis.warp import warp_image_with_gcps


def test_projective_warp_generates_geotiff_with_residuals(tmp_path) -> None:
    source_path = tmp_path / "source.png"
    output_path = tmp_path / "warped.tif"
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    image[:, :, 0] = 255
    Image.fromarray(image, mode="RGB").save(source_path)

    points = [
        WarpPoint(pixel_x=0, pixel_y=0, longitude=100.0, latitude=20.0),
        WarpPoint(pixel_x=10, pixel_y=0, longitude=100.01, latitude=20.0),
        WarpPoint(pixel_x=10, pixel_y=10, longitude=100.01, latitude=20.01),
        WarpPoint(pixel_x=0, pixel_y=10, longitude=100.0, latitude=20.01),
    ]

    result = warp_image_with_gcps(
        source_path,
        output_path,
        points,
        transform_type=TRANSFORM_PROJECTIVE,
    )

    assert output_path.exists()
    assert result.transform_type == TRANSFORM_PROJECTIVE
    assert result.rms_meters < 1.0
    assert all(residual.residual_meters < 1.0 for residual in result.residuals)

    with rasterio.open(output_path) as dataset:
        assert dataset.crs.to_string() == "EPSG:3857"
        assert dataset.width > 0
        assert dataset.height > 0
