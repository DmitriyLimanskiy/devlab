import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from app.api.auth.dependencies import get_current_user
from app.api.auth.models import AuthSession, User
from app.api.auth.schemas import LoginReq, LoginRes, RegisterReq, RegisterRes
from app.api.auth.services import Authorization
from app.db.session import get_session
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import delete, select
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


@router.post("/login", response_model=LoginRes)
async def login(
    payload: LoginReq,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> LoginRes:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not await run_in_threadpool(
        Authorization.verify_password, payload.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    token = secrets.token_urlsafe(32)
    token_hash = Authorization.session_hash(token)
    session_ttl_seconds = 7 * 24 * 60 * 60

    session = AuthSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(seconds=session_ttl_seconds),
    )

    db.add(session)
    await db.commit()

    response.set_cookie(
        key=Authorization.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # Для локального HTTP
        samesite="lax",
        path=Authorization.SESSION_COOKIE_PATH,
        max_age=session_ttl_seconds,
    )

    return LoginRes.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    db: Annotated[AsyncSession, Depends(get_session)],
    token: Annotated[
        str | None, Cookie(alias=Authorization.SESSION_COOKIE_NAME)
    ] = None,
) -> Response:
    if token and token.isascii():
        await db.execute(
            delete(AuthSession).where(
                AuthSession.token_hash == Authorization.session_hash(token)
            )
        )
        await db.commit()

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        key=Authorization.SESSION_COOKIE_NAME,
        path=Authorization.SESSION_COOKIE_PATH,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/me", response_model=LoginRes)
async def me(user: Annotated[User, Depends(get_current_user)]) -> LoginRes:
    return LoginRes.model_validate(user)
