from fastapi import Response

from app.config import get_settings

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"

# The refresh cookie is scoped to /auth so it is only sent to the refresh/logout
# endpoints, never to ordinary protected routes.
_REFRESH_PATH = "/auth"
_ACCESS_PATH = "/"


def _secure() -> bool:
    return get_settings().ENVIRONMENT == "production"


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    settings = get_settings()
    secure = _secure()
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=int(settings.access_token_timedelta.total_seconds()),
        httponly=True,
        secure=secure,
        samesite="lax",
        path=_ACCESS_PATH,
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=int(settings.refresh_token_timedelta.total_seconds()),
        httponly=True,
        secure=secure,
        samesite="lax",
        path=_REFRESH_PATH,
    )


def set_access_cookie(response: Response, access_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=int(settings.access_token_timedelta.total_seconds()),
        httponly=True,
        secure=_secure(),
        samesite="lax",
        path=_ACCESS_PATH,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE_NAME, path=_ACCESS_PATH)
    response.delete_cookie(REFRESH_COOKIE_NAME, path=_REFRESH_PATH)
