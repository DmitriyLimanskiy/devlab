from typing import Annotated

from app.api.auth.models import User
from app.api.auth.services import Authorization
from app.db.session import get_session
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_session)],
    token: Annotated[
        str | None, Cookie(alias=Authorization.SESSION_COOKIE_NAME)
    ] = None,
) -> User:
    user = await Authorization.find_user_by_session(db, token) if token else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется вход",
        )
    return user
