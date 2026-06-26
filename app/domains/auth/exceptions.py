class AuthError(Exception):
    """Base error for auth domain."""


class EmailAlreadyExistsError(AuthError):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email already registered: {email}")
