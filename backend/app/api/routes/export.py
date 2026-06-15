import mimetypes
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.export_artifact import ExportArtifactRead
from app.schemas.export_artifact import GeoTiffExportRequest
from app.schemas.export_artifact import XyzExportRequest
from app.services.export_service import export_geotiff
from app.services.export_service import export_xyz_tiles
from app.services.export_service import get_export_artifact
from app.services.export_service import get_export_artifact_path
from app.services.export_service import list_export_artifacts

router = APIRouter(prefix="/export")


@router.post("/geotiff", response_model=ApiResponse[ExportArtifactRead])
def export_geotiff_endpoint(
    payload: GeoTiffExportRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[ExportArtifactRead]:
    artifact = export_geotiff(db, payload.project_id)
    return ApiResponse(data=ExportArtifactRead.model_validate(artifact))


@router.post("/xyz", response_model=ApiResponse[ExportArtifactRead])
def export_xyz_endpoint(
    payload: XyzExportRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[ExportArtifactRead]:
    artifact = export_xyz_tiles(
        db,
        payload.project_id,
        payload.min_zoom,
        payload.max_zoom,
    )
    return ApiResponse(data=ExportArtifactRead.model_validate(artifact))


@router.get("/list", response_model=ApiResponse[list[ExportArtifactRead]])
def list_export_artifacts_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse[list[ExportArtifactRead]]:
    artifacts = list_export_artifacts(db, project_id)
    return ApiResponse(
        data=[ExportArtifactRead.model_validate(artifact) for artifact in artifacts]
    )


@router.get("/{artifact_id}", response_model=ApiResponse[ExportArtifactRead])
def get_export_artifact_endpoint(
    artifact_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse[ExportArtifactRead]:
    artifact = get_export_artifact(db, artifact_id)
    return ApiResponse(data=ExportArtifactRead.model_validate(artifact))


@router.get("/{artifact_id}/download")
def download_export_artifact_endpoint(
    artifact_id: UUID,
    db: Session = Depends(get_db),
) -> FileResponse:
    artifact = get_export_artifact(db, artifact_id)
    path = get_export_artifact_path(db, artifact_id)
    media_type = mimetypes.guess_type(artifact.file_name)[0] or "application/octet-stream"
    return FileResponse(
        path,
        filename=artifact.file_name,
        media_type=media_type,
    )
