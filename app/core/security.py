from passlib.context import CryptContext

from app.config import get_settings


settings = get_settings()


class PasswordSecurity:
    def __init__(self) -> None:
        self.pwd_context = CryptContext(schemes=["argon2"], default="argon2", deprecated="auto")

    def generate_password_hash(self, password: str) -> str:
        hashed_pass: str = self.pwd_context.hash(password)
        return hashed_pass

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        is_valid_password: bool = self.pwd_context.verify(plain_password, hashed_password)
        return is_valid_password

    def needs_rehash(self, hashed_password: str) -> bool:
        needs_rehash: bool = self.pwd_context.needs_update(hashed_password)
        return needs_rehash

    def generate_token_hash(self, token: str) -> str:
        hashed_token: str = self.pwd_context.hash(token)
        return hashed_token

    def verify_token_hash(self, token: str, hashed_token: str) -> bool:
        is_valid: bool = self.pwd_context.verify(token, hashed_token)
        return is_valid
