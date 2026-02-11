"""bcrypt password hasher for secure credential storage."""

import bcrypt


class BcryptPasswordHasher:
    """Hashes and verifies passwords using bcrypt.

    bcrypt is a one-way hashing algorithm — you can't recover the original
    password from the hash. Each hash includes a random salt, so the same
    password produces different hashes every time. Verification works by
    re-hashing the candidate password with the stored salt and comparing.
    """

    def hash(self, password: str) -> str:
        """Hash a plaintext password. Returns the bcrypt hash string."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify(self, password: str, hashed: str) -> bool:
        """Check if a plaintext password matches a bcrypt hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
