import hashlib

from app.api.auth.models import AuthSession, User
from pwdlib import PasswordHash
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

_password_hasher = PasswordHash.recommended()


class Authorization:
    SESSION_COOKIE_NAME = "session_token"
    SESSION_COOKIE_PATH = "/api/v1"

    @staticmethod
    def password_hash(password: SecretStr) -> str:
        """Хешировать пароль для хранения в базе"""
        return _password_hasher.hash(password.get_secret_value())

    @staticmethod
    def verify_password(password: SecretStr, password_hash: str) -> bool:
        """Проверить пароль по сохранённому хешу"""
        return _password_hasher.verify(password.get_secret_value(), password_hash)

    @staticmethod
    def session_hash(token: str) -> str:
        """Хешировать токен сессии для хранения в базе"""
        return hashlib.sha256(token.encode("ascii")).hexdigest()

    @staticmethod
    async def find_user_by_session(db: AsyncSession, token: str) -> User | None:
        """Найти пользователя по действующей сессии"""
        if not token or not token.isascii():
            return None

        return await db.scalar(
            select(User)
            .join(AuthSession, AuthSession.user_id == User.id)
            .where(
                AuthSession.token_hash == Authorization.session_hash(token),
                AuthSession.expires_at > func.now(),
            )
        )
