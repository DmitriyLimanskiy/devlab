from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["git-course"])


@router.get("/git-course")
def git_course():
    return {"data": "data"}
