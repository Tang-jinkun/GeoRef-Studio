from fastapi import APIRouter

from app.api.routes import control_point
from app.api.routes import export
from app.api.routes import georef
from app.api.routes import health
from app.api.routes import image
from app.api.routes import project

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(image.router, tags=["image"])
api_router.include_router(project.router, tags=["project"])
api_router.include_router(control_point.router, tags=["control-point"])
api_router.include_router(georef.router, tags=["georef"])
api_router.include_router(export.router, tags=["export"])
