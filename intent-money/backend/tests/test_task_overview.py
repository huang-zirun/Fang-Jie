import uuid
from collections.abc import AsyncGenerator
from datetime import timedelta

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
from app.utils.time import utc_day_start_naive, utc_now_naive


@pytest.mark.asyncio
async def test_task_overview_matches_dashboard_contract_and_keeps_admin_stats_protected():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user_id = uuid.uuid4()
    intent_traffic_id = uuid.uuid4()
    intent_sale_id = uuid.uuid4()
    platform_id = uuid.uuid4()
    today = utc_now_naive()
    yesterday = utc_day_start_naive() - timedelta(hours=1)

    task_pending_id = uuid.uuid4()
    task_published_id = uuid.uuid4()
    task_diagnosed_id = uuid.uuid4()
    task_old_id = uuid.uuid4()

    async with session_factory() as db:
        db.add_all(
            [
                User(id=user_id, is_anonymous=True, role="user"),
                Intent(id=intent_traffic_id, name="traffic", description="traffic", sort_order=1, is_active=True),
                Intent(id=intent_sale_id, name="sale", description="sale", sort_order=2, is_active=True),
                Platform(id=platform_id, name="xhs", is_active=True),
                ContentTask(
                    id=task_pending_id,
                    user_id=user_id,
                    intent_id=intent_traffic_id,
                    platform_id=platform_id,
                    status="PENDING",
                    task_type="image",
                    hook_text="hook",
                    storyboard=[{"shot": 1, "description": "shot description", "duration": "3s"}],
                    script_text="script",
                    title="title",
                    comment_template="comment",
                    why_it_works="reason",
                    swap_count=1,
                    created_at=today,
                ),
                ContentTask(
                    id=task_published_id,
                    user_id=user_id,
                    intent_id=intent_sale_id,
                    platform_id=platform_id,
                    status="PUBLISHED",
                    task_type="image",
                    hook_text="hook",
                    storyboard=[{"shot": 1, "description": "shot description", "duration": "3s"}],
                    script_text="script",
                    title="title",
                    comment_template="comment",
                    why_it_works="reason",
                    created_at=today,
                ),
                ContentTask(
                    id=task_diagnosed_id,
                    user_id=user_id,
                    intent_id=intent_sale_id,
                    platform_id=platform_id,
                    status="DIAGNOSED",
                    task_type="image",
                    hook_text="hook",
                    storyboard=[{"shot": 1, "description": "shot description", "duration": "3s"}],
                    script_text="script",
                    title="title",
                    comment_template="comment",
                    why_it_works="reason",
                    swap_count=2,
                    created_at=today,
                ),
                ContentTask(
                    id=task_old_id,
                    user_id=user_id,
                    intent_id=intent_traffic_id,
                    platform_id=platform_id,
                    status="PENDING",
                    task_type="image",
                    hook_text="hook",
                    storyboard=[{"shot": 1, "description": "shot description", "duration": "3s"}],
                    script_text="script",
                    title="title",
                    comment_template="comment",
                    why_it_works="reason",
                    swap_count=5,
                    created_at=yesterday,
                ),
            ]
        )
        await db.commit()
        db.add_all(
            [
                DiagnosisResult(
                    task_id=task_published_id,
                    problem_type="hook_weak",
                    problem_desc="hook weak",
                    optimization_direction="improve hook",
                    optimization_detail="use a stronger opening",
                ),
                DiagnosisResult(
                    task_id=task_diagnosed_id,
                    problem_type="normal",
                    problem_desc="normal",
                    optimization_direction="keep going",
                    optimization_detail="keep the current approach",
                ),
                DiagnosisResult(
                    task_id=task_old_id,
                    problem_type="conversion_weak",
                    problem_desc="conversion weak",
                    optimization_direction="improve conversion",
                    optimization_detail="use a clearer conversion CTA",
                ),
            ]
        )
        await db.commit()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as db:
            yield db

    async def override_get_current_user() -> User:
        return User(id=user_id, is_anonymous=True, role="user")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            overview_response = await client.get("/api/v1/tasks/overview")
            admin_response = await client.get("/api/v1/admin/stats")

        assert overview_response.status_code == 200
        data = overview_response.json()
        assert data["today_tasks"] == 3
        assert data["today_published"] == 2
        assert data["today_pending"] == 1
        assert data["today_swapped"] == 3
        assert data["intent_distribution"] == [
            {"intent_name": "sale", "count": 2},
            {"intent_name": "traffic", "count": 1},
        ]
        assert data["total_problems"] == 2
        assert data["problem_stats"] == [
            {"problem_type": "conversion_weak", "count": 1},
            {"problem_type": "hook_weak", "count": 1},
        ]

        assert admin_response.status_code == 403
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
