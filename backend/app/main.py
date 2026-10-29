from app.routes.courses.catalog import router as catalog_router
from app.routes.courses.git import router as git_router
from fastapi import APIRouter, FastAPI

app = FastAPI(title="DevLab", docs_url=None, redoc_url=None, openapi_url=None)


router = APIRouter(prefix="/api/v1")


# @router.get("/main")
# def home() -> dict[str, str]:
#     return {
#         "name": "DevLab",
#         "description": "Курсы по технологиям и инструменты для практики.",
#     }


app.include_router(router)
app.include_router(catalog_router)
app.include_router(git_router)
