"""CLI commands for Talent Inbound OS administration.

Usage:
    python -m talent_inbound.cli reset-password --email user@example.com
"""

import argparse
import asyncio
import sys

from sqlalchemy import select, update

from talent_inbound.config import get_settings
from talent_inbound.modules.auth.infrastructure.orm_models import UserModel
from talent_inbound.modules.auth.infrastructure.password import BcryptPasswordHasher
from talent_inbound.shared.infrastructure.database import (
    create_engine,
    create_session_factory,
)


async def reset_password(email: str) -> None:
    """Reset a user's password by email. Prompts for the new password."""
    import getpass

    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    session_factory = create_session_factory(engine)

    new_password = getpass.getpass("New password: ")
    confirm = getpass.getpass("Confirm password: ")

    if new_password != confirm:
        print("Error: Passwords do not match.")
        sys.exit(1)

    if len(new_password) < 8:
        print("Error: Password must be at least 8 characters.")
        sys.exit(1)

    hasher = BcryptPasswordHasher()
    hashed = hasher.hash(new_password)

    async with session_factory() as session:
        # Check user exists
        result = await session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        user = result.scalar_one_or_none()

        if user is None:
            print(f"Error: No user found with email '{email}'.")
            sys.exit(1)

        # Update password
        await session.execute(
            update(UserModel)
            .where(UserModel.id == user.id)
            .values(hashed_password=hashed)
        )
        await session.commit()

    await engine.dispose()
    print(f"Password reset successfully for '{email}'.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="talent_inbound.cli",
        description="Talent Inbound OS administration CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # reset-password
    rp = subparsers.add_parser("reset-password", help="Reset a user's password")
    rp.add_argument("--email", required=True, help="User email address")

    args = parser.parse_args()

    if args.command == "reset-password":
        asyncio.run(reset_password(args.email))


if __name__ == "__main__":
    main()
