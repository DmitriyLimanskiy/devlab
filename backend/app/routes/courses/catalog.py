from app.models.courses.catalog import ResCatalog
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/catalog", response_model=list[ResCatalog])
def catalog() -> list[ResCatalog]:
    return [
        ResCatalog(
            id="git",
            title="Git",
            description="Контроль версий и работа с репозиториями.",
        )
    ]
