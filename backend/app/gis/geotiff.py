from pathlib import Path

import rasterio
from affine import Affine


DEFAULT_CRS = "EPSG:4326"


def affine_matrix_to_transform(matrix: list[list[float]]) -> Affine:
    if len(matrix) != 2 or any(len(row) != 3 for row in matrix):
        raise ValueError("Affine matrix must be 2x3")

    return Affine(
        matrix[0][0],
        matrix[0][1],
        matrix[0][2],
        matrix[1][0],
        matrix[1][1],
        matrix[1][2],
    )


def write_geotiff(
    source_path: Path,
    output_path: Path,
    matrix: list[list[float]],
    crs: str = DEFAULT_CRS,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    transform = affine_matrix_to_transform(matrix)

    with rasterio.open(source_path) as source:
        profile = source.profile.copy()
        profile.update(
            driver="GTiff",
            crs=crs,
            transform=transform,
            compress="deflate",
        )

        with rasterio.open(output_path, "w", **profile) as target:
            target.write(source.read())
