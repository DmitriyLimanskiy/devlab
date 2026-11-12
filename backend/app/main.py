from app.api.auth.routers import router as register_router
from app.api.catalog.routers import router as catalog_router
from app.api.courses.routers.git_course import router as git_router
from fastapi import FastAPI

app = FastAPI(
    title="Stack Forge",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.include_router(catalog_router)
app.include_router(git_router)
app.include_router(register_router)


@app.get("/api/v1/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}
