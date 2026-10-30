"""Создание приложения и регистрация HTTP-маршрутов."""
from fastapi import FastAPI

from app.api.routes.course_catalog import router as catalog_router
from app.api.routes.git_course import router as git_router

app = FastAPI(title="DevLab", docs_url=None, redoc_url=None, openapi_url=None)

app.include_router(catalog_router)
app.include_router(git_router)
