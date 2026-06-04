import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.database import Base, get_db
from app.main import app
from app.models.user import User


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def test_user_id():
    return uuid.uuid4()


@pytest_asyncio.fixture
async def client(test_engine, test_user_id):
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as db:
            yield db

    async def override_get_current_user() -> User:
        return User(id=test_user_id, is_anonymous=True, role="user")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_accounts_empty(client):
    resp = await client.get("/api/v1/accounts/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_import_cookie_invalid_platform(client):
    resp = await client.post(
        "/api/v1/accounts/wechat/cookie",
        json={"cookie_data": "test=123"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_unbind_nonexistent_account(client):
    resp = await client.delete("/api/v1/accounts/xhs")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_validate_nonexistent_account(client):
    resp = await client.post("/api/v1/accounts/douyin/validate")
    assert resp.status_code == 404
