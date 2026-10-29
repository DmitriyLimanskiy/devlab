from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

app = FastAPI(title="DevLab", docs_url=None, redoc_url=None, openapi_url=None)


router = APIRouter(prefix="/api/v1")


class Course(BaseModel):
    id: str
    title: str
    description: str
    status: str = "planned"


@router.get("/")
def home() -> dict[str, str]:
    return {"name": "DevLab", "description": "Курсы по технологиям и инструменты для практики."}


@router.get("/courses", response_model=list[Course])
def courses() -> list[Course]:
    # Стартовый каталог шаблона. Учебные материалы пока не реализованы.
    return [
        Course(id="git", title="Git", description="Контроль версий и работа с репозиториями."),
        Course(id="python", title="Python", description="Основы программирования на Python."),
        Course(id="docker", title="Docker", description="Контейнеризация приложений."),
    ]


app.include_router(router)
