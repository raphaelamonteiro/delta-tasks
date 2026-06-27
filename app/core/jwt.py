from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import InvalidTokenError

from app.config import get_settings


class TokenError(Exception):
    """Raised when a JWT is missing, malformed, expired or of an unexpected type."""


class JWTService:
    """Stateless JSON Web Token encoding/decoding for access and refresh tokens.

    Access and refresh tokens are signed with independent keys so that leaking
    one does not compromise the other. No token is persisted: validity is derived
    entirely from the signature and the ``exp`` claim.
    """

    ACCESS_TYPE = "access"
    REFRESH_TYPE = "refresh"

    def __init__(self) -> None:
        settings = get_settings()
        self.algorithm = settings.JWT_ALGORITHM
        self.access_key = settings.ACCESS_TOKEN_SIGNING_KEY
        self.refresh_key = settings.REFRESH_TOKEN_SIGNING_KEY
        self.access_ttl = settings.access_token_timedelta
        self.refresh_ttl = settings.refresh_token_timedelta

    def create_access_token(self, subject: str, claims: dict[str, Any] | None = None) -> str:
        return self._encode(subject, self.ACCESS_TYPE, self.access_key, self.access_ttl, claims)

    def create_refresh_token(self, subject: str) -> str:
        return self._encode(subject, self.REFRESH_TYPE, self.refresh_key, self.refresh_ttl, None)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        return self._decode(token, self.ACCESS_TYPE, self.access_key)

    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        return self._decode(token, self.REFRESH_TYPE, self.refresh_key)

    def _encode(
        self,
        subject: str,
        token_type: str,
        key: str,
        ttl: timedelta,
        claims: dict[str, Any] | None,
    ) -> str:
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": subject,
            "type": token_type,
            "iat": now,
            "exp": now + ttl,
        }
        if claims:
            payload.update(claims)
        return jwt.encode(payload, key, algorithm=self.algorithm)

    def _decode(self, token: str, expected_type: str, key: str) -> dict[str, Any]:
        try:
            payload: dict[str, Any] = jwt.decode(token, key, algorithms=[self.algorithm])
        except InvalidTokenError as exc:
            raise TokenError("Invalid or expired token") from exc

        if payload.get("type") != expected_type:
            raise TokenError("Unexpected token type")
        return payload
