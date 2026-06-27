class AuthError(Exception):
    """Base error for auth domain."""


class EmailAlreadyExistsError(AuthError):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email already registered: {email}")


class InvalidCredentialsError(AuthError):
    """Raised when the email/password pair does not match an active account."""


class InactiveUserError(AuthError):
    def __init__(self, user_id: object) -> None:
        self.user_id = user_id
        super().__init__(f"User account is inactive: {user_id}")


class SamePasswordError(AuthError):
    """Raised when the new password is equal to the current one."""
