"""Database engine, session factory, declarative base, and per-request session middleware."""

from contextvars import ContextVar
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

logger = structlog.get_logger()

# ContextVar holding the current request's DB session
_current_session: ContextVar[AsyncSession | None] = ContextVar(
    "_current_session", default=None
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""


def create_engine(database_url: str, echo: bool = False):
    return create_async_engine(database_url, echo=echo, future=True)


def create_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def get_current_session() -> AsyncSession:
    """Retrieve the per-request DB session from the ContextVar.

    Called by the DI container on every repo/use-case construction,
    returning the session that DBSessionMiddleware created for this request.
    """
    session = _current_session.get()
    if session is None:
        raise RuntimeError(
            "No database session available. Is DBSessionMiddleware configured?"
        )
    return session


class DBSessionMiddleware:
    """Pure ASGI middleware: creates one AsyncSession per HTTP request,
    stores it in a ContextVar, commits on success, rolls back on error."""

    def __init__(
        self,
        app: Any,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.app = app
        self.session_factory = session_factory

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async with self.session_factory() as session:
            token = _current_session.set(session)
            try:
                await self.app(scope, receive, send)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                _current_session.reset(token)
