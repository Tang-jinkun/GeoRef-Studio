import shutil
import subprocess
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
ARTIFACT_TYPE_XYZ_ZIP = "XYZ ZIP"
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


def _latest_geotiff_artifact(db: Session, project_id: UUID) -> ExportArtifact | None:
    statement = (
        select(ExportArtifact)
        .where(
            ExportArtifact.project_id == project_id,
            ExportArtifact.artifact_type == ARTIFACT_TYPE_GEOTIFF,
            ExportArtifact.status == ARTIFACT_STATUS_COMPLETED,
        )
        .order_by(ExportArtifact.create_time.desc(), ExportArtifact.id.desc())
    )
    for artifact in db.scalars(statement).all():
        if Path(artifact.storage_path).exists():
            return artifact
    return None


def _get_or_create_geotiff_artifact(db: Session, project_id: UUID) -> ExportArtifact:
    artifact = _latest_geotiff_artifact(db, project_id)
    if artifact is not None:
        return artifact
    return export_geotiff(db, project_id)


def export_xyz_tiles(
    db: Session,
    project_id: UUID,
    min_zoom: int = 0,
    max_zoom: int = 6,
) -> ExportArtifact:
    project = _get_project_or_404(db, project_id)
    if max_zoom < min_zoom:
        raise HTTPException(
            status_code=400,
            detail="max_zoom must be greater than or equal to min_zoom",
        )

    geotiff_artifact = _get_or_create_geotiff_artifact(db, project.id)
    geotiff_path = Path(geotiff_artifact.storage_path)
    if not geotiff_path.exists():
        raise HTTPException(status_code=404, detail="GeoTIFF file not found")

    output_dir = _outputs_dir(project.id)
    run_id = uuid4().hex[:8]
    tiles_dir = output_dir / f"xyz_z{min_zoom}-{max_zoom}_{run_id}"
    file_name = f"{project.id}_xyz_z{min_zoom}-{max_zoom}_{run_id}.zip"
    archive_base = output_dir / file_name.removesuffix(".zip")
    archive_path = output_dir / file_name

    try:
        tiles_dir.mkdir(parents=True, exist_ok=False)
        subprocess.run(
            [
                "gdal2tiles.py",
                "--xyz",
                "-w",
                "none",
                "--processes=1",
                "--tilesize=256",
                "-r",
                "bilinear",
                "-z",
                f"{min_zoom}-{max_zoom}",
                str(geotiff_path),
                str(tiles_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        shutil.make_archive(str(archive_base), "zip", tiles_dir)
    except subprocess.CalledProcessError as exc:
        if archive_path.exists():
            archive_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"XYZ tile export failed: {exc.stderr.strip() or exc.stdout.strip()}",
        ) from exc
    except OSError as exc:
        if archive_path.exists():
            archive_path.unlink()
        raise HTTPException(
            status_code=500,
            detail="XYZ tile archive failed",
        ) from exc
    finally:
        shutil.rmtree(tiles_dir, ignore_errors=True)

    artifact = ExportArtifact(
        project_id=project.id,
        artifact_type=ARTIFACT_TYPE_XYZ_ZIP,
        file_name=file_name,
        storage_path=str(archive_path),
        size_bytes=archive_path.stat().st_size,
        status=ARTIFACT_STATUS_COMPLETED,
        message=f"z{min_zoom}-{max_zoom}",
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
