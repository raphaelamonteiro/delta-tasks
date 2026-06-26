from typing import Any

from fastapi import status

from app.domains.auth.schemas import RegisterUserResponse

register_responses: dict[int | str, dict[str, Any]] = {
    201: {
        "description": "User registered successfully.",
    },
    409: {
        "description": "Email already registered.",
    },
    422: {
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
