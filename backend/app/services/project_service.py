from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.models.export_artifact import ExportArtifact
from app.models.image_file import ImageFile
from app.models.project import Project
from app.schemas.project import ProjectCreate


def create_project(db: Session, payload: ProjectCreate) -> Project:
    image_file = db.get(ImageFile, payload.image_id)
    if image_file is None:
        raise HTTPException(status_code=404, detail="Image file not found")

    project = Project(
        name=payload.name.strip(),
        description=payload.description,
        image_id=image_file.id,
        image_path=image_file.storage_path,
        status="未配准",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return get_project(db, project.id)


def list_projects(db: Session) -> list[Project]:
    statement = (
        select(Project)
        .options(joinedload(Project.image))
        .order_by(Project.create_time.desc())
    )
    return list(db.scalars(statement).all())


def get_project(db: Session, project_id: UUID) -> Project:
    statement = (
        select(Project)
        .options(joinedload(Project.image))
        .where(Project.id == project_id)
    )
    project = db.scalars(statement).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def delete_project(db: Session, project_id: UUID) -> None:
    project = get_project(db, project_id)
    image_id = project.image_id
    image_path = Path(project.image_path)

    artifact_paths = [
        Path(path)
        for path in db.scalars(
            select(ExportArtifact.storage_path).where(ExportArtifact.project_id == project.id)
        ).all()
    ]
    if project.georef_result_path:
        georef_path = Path(project.georef_result_path)
        artifact_paths.extend([georef_path, georef_path.with_name("georef_preview.png")])

    db.delete(project)
    db.flush()

    remaining_image_refs = db.scalar(
        select(func.count()).select_from(Project).where(Project.image_id == image_id)
    )
    image_file = db.get(ImageFile, image_id)
    if remaining_image_refs == 0 and image_file is not None:
        db.delete(image_file)

    db.commit()

    for artifact_path in artifact_paths:
        artifact_path.unlink(missing_ok=True)
        try:
            artifact_path.parent.rmdir()
        except OSError:
            pass

    if remaining_image_refs == 0:
        image_path.unlink(missing_ok=True)
