import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_user
from app.database import Base, get_db
from app.main import app
from app.models.content_task import ContentTask
from app.models.diagnosis_result import DiagnosisResult
from app.models.intent import Intent
from app.models.platform import Platform
from app.models.user import User


@pytest.mark.asyncio
async def test_next_task_accepts_json_body_and_defaults_to_current_platform():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user_id = uuid.uuid4()
    intent_id = uuid.uuid4()
    platform_id = uuid.uuid4()
    task_id = uuid.uuid4()

    async with session_factory() as db:
        user = User(id=user_id, is_anonymous=True)
        db.add_all(
            [
                user,
                Intent(id=intent_id, name="traffic", description="test intent", sort_order=1, is_active=True),
                Platform(id=platform_id, name="xhs", is_active=True),
                ContentTask(
                    id=task_id,
                    user_id=user_id,
                    intent_id=intent_id,
                    platform_id=platform_id,
                    status="DIAGNOSED",
                    task_type="image",
                    hook_text="old hook",
                    storyboard=[{"shot": 1, "description": "old shot", "duration": "3s"}],
                    script_text="old script",
                    title="old title",
                    comment_template="old comment",
                    why_it_works="old reason",
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                ),
            ]
        )
        await db.commit()
        db.add(
            DiagnosisResult(
                task_id=task_id,
                problem_type="hook_weak",
                problem_desc="hook weak",
                optimization_direction="improve hook",
                optimization_detail="use a stronger opening",
            )
        )
        await db.commit()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as db:
            yield db

    async def override_get_current_user() -> User:
        return User(id=user_id, is_anonymous=True)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/tasks/{task_id}/next", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["prev_task_id"] == str(task_id)
        assert data["platform_id"] == str(platform_id)
        assert data["task_type"] == "image"
        assert data["is_optimized"] is True
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
