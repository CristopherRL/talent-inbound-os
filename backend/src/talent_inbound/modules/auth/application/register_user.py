"""RegisterUser use case — creates a new user account."""

from dataclasses import dataclass

from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.domain.events import UserRegistered
from talent_inbound.modules.auth.domain.exceptions import DuplicateEmailError
from talent_inbound.modules.auth.domain.repositories import UserRepository
from talent_inbound.modules.auth.infrastructure.password import BcryptPasswordHasher
from talent_inbound.shared.infrastructure.event_bus import InProcessEventBus


@dataclass
class RegisterUserCommand:
    email: str
    password: str


class RegisterUser:
    """Validates email uniqueness, hashes password, persists user, publishes event."""

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: BcryptPasswordHasher,
        event_bus: InProcessEventBus,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._event_bus = event_bus

    async def execute(self, command: RegisterUserCommand) -> User:
        existing = await self._user_repo.find_by_email(command.email)
        if existing:
            raise DuplicateEmailError(command.email)

        user = User(
            email=command.email,
            hashed_password=self._password_hasher.hash(command.password),
        )

        saved_user = await self._user_repo.save(user)

        event = UserRegistered(user_id=saved_user.id, email=saved_user.email)
        saved_user.add_event(event)
        await self._event_bus.publish_all(saved_user.collect_events())

        return saved_user
