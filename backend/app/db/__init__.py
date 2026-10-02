from collections.abc import Iterator
from functools import lru_cache

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session_factory(request: Request) -> sessionmaker[Session]:
    """FastAPI dependency: the app's session factory (tests swap in their own)."""
    return request.app.state.session_factory


def get_session(request: Request) -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    with get_session_factory(request)() as session:
        yield session
