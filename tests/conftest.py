from collections.abc import AsyncGenerator, Awaitable, Callable

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.core.security import PasswordSecurity
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.dependencies import get_postgres_session
from app.db.models import GlobalRole, User
from app.main import create_app

DEFAULT_PASSWORD = "Sup3rSecret!"

_SECURITY = PasswordSecurity()

UserFactory = Callable[..., Awaitable[User]]


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    eng = create_async_engine(get_settings().test_database_url, future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_postgres_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
def make_user(db_session: AsyncSession) -> UserFactory:
    async def _make(
        *,
        name: str = "User",
        email: str = "user@example.com",
        password: str = DEFAULT_PASSWORD,
        role: GlobalRole = GlobalRole.USER,
        is_active: bool = True,
    ) -> User:
        user = User(
            name=name,
            email=email,
            password_hash=_SECURITY.generate_password_hash(password),
            global_role=role,
            is_active=is_active,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _make


@pytest_asyncio.fixture
async def admin_user(make_user: UserFactory) -> User:
    return await make_user(name="Admin", email="admin@example.com", role=GlobalRole.ADMIN)


@pytest_asyncio.fixture
async def regular_user(make_user: UserFactory) -> User:
    return await make_user(name="Regular", email="regular@example.com", role=GlobalRole.USER)


async def login_as(client: AsyncClient, email: str, password: str = DEFAULT_PASSWORD) -> None:
    response = await client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
