from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

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

