from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.project import ProjectCreate
from app.schemas.project import ProjectRead
from app.services.project_service import create_project
from app.services.project_service import get_project
from app.services.project_service import list_projects

router = APIRouter(prefix="/project")


@router.post("/create", response_model=ApiResponse[ProjectRead])
def create_project_endpoint(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[ProjectRead]:
    project = create_project(db, payload)
    return ApiResponse(data=ProjectRead.model_validate(project))


@router.get("/list", response_model=ApiResponse[list[ProjectRead]])
def list_projects_endpoint(db: Session = Depends(get_db)) -> ApiResponse[list[ProjectRead]]:
    projects = list_projects(db)
    return ApiResponse(data=[ProjectRead.model_validate(project) for project in projects])


@router.get("/{project_id}", response_model=ApiResponse[ProjectRead])
def get_project_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse[ProjectRead]:
    project = get_project(db, project_id)
    return ApiResponse(data=ProjectRead.model_validate(project))

