from typing import Annotated

from app.api.auth.models import User
from app.api.auth.schemas import RegisterReq, RegisterRes
from app.api.auth.services import Authorization
from app.db.session import get_session
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register", response_model=RegisterRes, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: RegisterReq, db: Annotated[AsyncSession, Depends(get_session)]
) -> RegisterRes:
    password_hash = await run_in_threadpool(
        Authorization.password_hash, payload.password
    )

    statement = (
        insert(User)
        .values(email=payload.email, password_hash=password_hash)
        .on_conflict_do_nothing(index_elements=[User.email])
        .returning(User)
    )

    user = await db.scalar(statement)

    if user is None:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже зарегистрирован",
        )

    await db.commit()
    return RegisterRes.model_validate(user)


@router.get("/login")
async def login(): ...


@router.get("logout")
async def logout(): ...
