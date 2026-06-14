from pathlib import Path
from uuid import UUID
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.gis.geotiff import DEFAULT_CRS
from app.gis.geotiff import write_geotiff
from app.models.export_artifact import ExportArtifact
from app.models.project import Project

ARTIFACT_TYPE_GEOTIFF = "GeoTIFF"
ARTIFACT_STATUS_COMPLETED = "completed"


def _outputs_dir(project_id: UUID) -> Path:
    path = Path(settings.storage_root).resolve() / "outputs" / str(project_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_project_or_404(db: Session, project_id: UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def export_geotiff(db: Session, project_id: UUID) -> ExportArtifact:
    project = _get_project_or_404(db, project_id)
    if not project.transform_matrix:
        raise HTTPException(status_code=400, detail="Project is not georeferenced")

    source_path = Path(project.image_path)
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Source image file not found")

    file_name = f"{project.id}_{uuid4().hex[:8]}.tif"
    output_path = _outputs_dir(project.id) / file_name
    write_geotiff(source_path, output_path, project.transform_matrix, DEFAULT_CRS)

    artifact = ExportArtifact(
        project_id=project.id,
        artifact_type=ARTIFACT_TYPE_GEOTIFF,
        file_name=file_name,
        storage_path=str(output_path),
        size_bytes=output_path.stat().st_size,
        status=ARTIFACT_STATUS_COMPLETED,
        message=None,
    )
    project.status = "已导出"
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def list_export_artifacts(db: Session, project_id: UUID) -> list[ExportArtifact]:
    _get_project_or_404(db, project_id)
    statement = (
        select(ExportArtifact)
        .where(ExportArtifact.project_id == project_id)
        .order_by(ExportArtifact.create_time.desc(), ExportArtifact.id.desc())
    )
    return list(db.scalars(statement).all())


def get_export_artifact(db: Session, artifact_id: UUID) -> ExportArtifact:
    artifact = db.get(ExportArtifact, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Export artifact not found")
    return artifact


def get_export_artifact_path(db: Session, artifact_id: UUID) -> Path:
    artifact = get_export_artifact(db, artifact_id)
    path = Path(artifact.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Export file not found")
    return path
