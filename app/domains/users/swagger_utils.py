from typing import Any

from fastapi import status

from app.domains.users.schemas import UserListResponse, UserResponse

list_users_swagger: dict[str, Any] = {
    "summary": "List users",
    "description": "Returns a paginated list of users.",
    "response_model": UserListResponse,
    "responses": {
        200: {"description": "Users listed successfully."},
    },
}

get_user_swagger: dict[str, Any] = {
    "summary": "Get a user",
    "description": "Returns a single user by id.",
    "response_model": UserResponse,
    "responses": {
        200: {"description": "User found."},
        404: {"description": "User not found."},
    },
}

update_user_swagger: dict[str, Any] = {
    "summary": "Update a user",
    "description": ("Partially updates a user. " "Returns 409 if the new email is already taken."),
    "response_model": UserResponse,
    "responses": {
        200: {"description": "User updated successfully."},
        404: {"description": "User not found."},
        409: {"description": "Email already registered."},
        400: {"description": "Request body validation failed."},
    },
}

delete_user_swagger: dict[str, Any] = {
    "summary": "Delete a user",
    "description": (
        "Permanently deletes a user. " "Returns 409 if the user still has related records."
    ),
    "status_code": status.HTTP_204_NO_CONTENT,
    "responses": {
        204: {"description": "User deleted successfully."},
        404: {"description": "User not found."},
        409: {"description": "User has related records and cannot be deleted."},
    },
}
