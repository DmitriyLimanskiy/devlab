from app.api.auth.routers import router as register_router
from app.api.catalog.routers import router as catalog_router
from app.api.cli.routers.cli import router as cli_router
from app.api.cli.routers.worktree import router as cli_worktree_router
from app.api.cli.routers.worktree import ws_router as cli_worktree_ws_router
from app.api.courses.routers.git_course import router as git_router
from app.api.practice.routers.git_practice import router as practice_router
from app.api.practice.routers.git_practice import ws_router as practice_ws_router
from app.api.practice.routers.worktree import router as worktree_router
from app.api.practice.routers.worktree import ws_router as worktree_ws_router
from fastapi import FastAPI

app = FastAPI(
    title="Stack Forge",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.include_router(catalog_router)
app.include_router(git_router)
app.include_router(cli_router)
app.include_router(practice_router)
app.include_router(cli_worktree_router)
app.include_router(worktree_router)
app.include_router(cli_worktree_ws_router)
app.include_router(practice_ws_router)
app.include_router(worktree_ws_router)
app.include_router(register_router)
