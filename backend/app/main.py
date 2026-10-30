from app.api.routes.cli import router as cli
from app.api.routes.course_catalog import router as catalog_router
from app.api.routes.git_course import router as git_router
from fastapi import FastAPI

app = FastAPI(title="DevLab", docs_url=None, redoc_url=None, openapi_url=None)

app.include_router(catalog_router)
app.include_router(git_router)
app.include_router(cli)
