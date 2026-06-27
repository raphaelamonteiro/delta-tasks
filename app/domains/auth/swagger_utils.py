from typing import Any

from fastapi import status

from app.domains.auth.schemas import AuthenticatedUser, RegisterUserResponse

register_responses: dict[int | str, dict[str, Any]] = {
    201: {
        "description": "User registered successfully.",
    },
    401: {
        "description": "Not authenticated.",
    },
    403: {
        "description": "Admin privileges required.",
    },
    409: {
        "description": "Email already registered.",
    },
    400: {
        "description": "Request body validation failed.",
    },
}

register_user_swagger: dict[str, Any] = {
    "summary": "Register a user",
    "description": ("Creates a new user account. " "Returns 409 if the email is already taken."),
    "status_code": status.HTTP_201_CREATED,
    "response_model": RegisterUserResponse,
    "responses": register_responses,
}

login_swagger: dict[str, Any] = {
    "summary": "Log in",
    "description": (
        "Authenticates by email/password and sets HttpOnly access and refresh "
        "token cookies. Returns 401 for invalid credentials or inactive accounts, "
        "without revealing which check failed."
    ),
    "response_model": AuthenticatedUser,
    "responses": {
        200: {"description": "Authenticated; auth cookies set."},
        401: {"description": "Invalid credentials or inactive account."},
        400: {"description": "Request body validation failed."},
    },
}

refresh_swagger: dict[str, Any] = {
    "summary": "Refresh the access token",
    "description": (
        "Issues a new access token cookie using the refresh token cookie. "
        "Returns 401 if the refresh token is missing, invalid or expired."
    ),
    "response_model": AuthenticatedUser,
    "responses": {
        200: {"description": "Access token refreshed."},
        401: {"description": "Missing or invalid refresh token."},
    },
}

logout_swagger: dict[str, Any] = {
    "summary": "Log out",
    "description": "Clears the access and refresh token cookies.",
    "status_code": status.HTTP_204_NO_CONTENT,
    "responses": {
        204: {"description": "Logged out; auth cookies cleared."},
        401: {"description": "Not authenticated."},
    },
}

me_swagger: dict[str, Any] = {
    "summary": "Current user",
    "description": "Returns the authenticated user derived from the access token cookie.",
    "response_model": AuthenticatedUser,
    "responses": {
        200: {"description": "Current user."},
        401: {"description": "Not authenticated."},
    },
}

change_password_swagger: dict[str, Any] = {
    "summary": "Change own password",
    "description": (
        "Changes the authenticated user's own password. Requires the current "
        "password. Returns 401 if it is wrong, 400 if the new password is invalid "
        "or equal to the current one."
    ),
    "status_code": status.HTTP_204_NO_CONTENT,
    "responses": {
        204: {"description": "Password changed."},
        400: {"description": "Invalid new password."},
        401: {"description": "Not authenticated or wrong current password."},
    },
}
