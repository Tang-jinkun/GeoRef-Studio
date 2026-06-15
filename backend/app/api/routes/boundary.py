from pathlib import Path

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.schemas.boundary import BoundaryDatasetRead
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/boundary")


def _boundary_dir() -> Path:
    path = Path(settings.storage_root).resolve() / "boundaries"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _boundary_path(dataset_id: str) -> Path:
    safe_id = Path(dataset_id).stem
    if safe_id != dataset_id:
        raise HTTPException(status_code=400, detail="Invalid boundary dataset id")

    candidates = [
        _boundary_dir() / f"{safe_id}.geojson",
        _boundary_dir() / f"{safe_id}.json",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    raise HTTPException(status_code=404, detail="Boundary dataset not found")


@router.get("/list", response_model=ApiResponse[list[BoundaryDatasetRead]])
def list_boundary_datasets() -> ApiResponse[list[BoundaryDatasetRead]]:
    datasets = []
    for path in sorted([*_boundary_dir().glob("*.geojson"), *_boundary_dir().glob("*.json")]):
        datasets.append(
            BoundaryDatasetRead(
                id=path.stem,
                file_name=path.name,
                size_bytes=path.stat().st_size,
            )
        )
    return ApiResponse(data=datasets)


@router.get("/{dataset_id}/geojson")
def get_boundary_geojson(dataset_id: str) -> FileResponse:
    path = _boundary_path(dataset_id)
    return FileResponse(path, filename=path.name, media_type="application/geo+json")
