from pwdlib import PasswordHash
from pydantic import SecretStr

_password_hasher = PasswordHash.recommended()


class Authorization:
    @staticmethod
    def password_hash(password: SecretStr) -> str:
        """Хешировать пароль для хранения в базе"""
        return _password_hasher.hash(password.get_secret_value())
