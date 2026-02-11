"""Auth domain exceptions."""


class DuplicateEmailError(Exception):
    """Raised when trying to register with an already-used email."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email already registered: {email}")


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid.

    Uses a generic message to avoid revealing whether the email exists.
    """

    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class InactiveUserError(Exception):
    """Raised when an inactive user tries to authenticate."""

    def __init__(self) -> None:
        super().__init__("User account is inactive")
