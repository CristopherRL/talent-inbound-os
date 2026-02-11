"""SQLAlchemy implementation of the UserRepository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.domain.repositories import UserRepository
from talent_inbound.modules.auth.infrastructure.orm_models import UserModel


class SqlAlchemyUserRepository(UserRepository):
    """Adapter: persists User entities via SQLAlchemy async sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> User:
        model = UserModel.from_domain(user)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_domain()

    async def find_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def find_by_id(self, user_id: str) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None
