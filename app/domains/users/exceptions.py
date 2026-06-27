from uuid import UUID


class UserError(Exception):
    """Base error for users domain."""


class UserNotFoundError(UserError):
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        super().__init__(f"User not found: {user_id}")


class EmailAlreadyTakenError(UserError):
    def __init__(self, email: str | None) -> None:
        self.email = email
        super().__init__(f"Email already registered: {email}")


class UserHasDependenciesError(UserError):
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        super().__init__(f"User has related records and cannot be deleted: {user_id}")
