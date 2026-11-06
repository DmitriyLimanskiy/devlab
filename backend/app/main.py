from app.api.routes.catalog.catalog import router as catalog_router
from app.api.routes.cli.cli import router as cli_router
from app.api.routes.cli.worktree import router as cli_worktree_router
from app.api.routes.cli.worktree import ws_router as cli_worktree_ws_router
from app.api.routes.courses.git_course import router as git_router
from app.api.routes.practice.git_practice import router as practice_router
from app.api.routes.practice.git_practice import ws_router as practice_ws_router
from app.api.routes.practice.worktree import router as worktree_router
from app.api.routes.practice.worktree import ws_router as worktree_ws_router
from fastapi import FastAPI

app = FastAPI(
    title="DevLab",
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
