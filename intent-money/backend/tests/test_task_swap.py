import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.content_task import ContentTask
from app.models.intent import Intent
from app.models.platform import Platform
from app.models.user import User
from app.api.v1.tasks import swap_task
from app.services.task_service import generate_task


@pytest.mark.asyncio
async def test_generate_task_rejects_pending_task_with_sqlite_naive_datetime():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user_id = uuid.uuid4()
    intent_id = uuid.uuid4()
    platform_id = uuid.uuid4()

    async with session_factory() as db:
        db.add_all(
            [
                User(id=user_id, is_anonymous=True),
                Intent(id=intent_id, name="引流拿客户", description="测试意图", sort_order=1, is_active=True),
                Platform(id=platform_id, name="抖音", is_active=True),
                ContentTask(
                    user_id=user_id,
                    intent_id=intent_id,
                    platform_id=platform_id,
                    status="PENDING",
                    task_type="video",
                    hook_text="旧任务",
                    storyboard=[{"shot": 1, "description": "测试", "duration": "3s"}],
                    script_text="旧任务文案",
                    title="旧任务标题",
                    comment_template="旧任务评论",
                    why_it_works="旧任务原因",
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                ),
            ]
        )
        await db.commit()

        with pytest.raises(ValueError, match="HAS_PENDING_TASK"):
            await generate_task(db, user_id, intent_id, platform_id)

    await engine.dispose()


@pytest.mark.asyncio
async def test_swap_task_accepts_sqlite_naive_created_at():
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
                Intent(id=intent_id, name="引流拿客户", description="测试意图", sort_order=1, is_active=True),
                Platform(id=platform_id, name="抖音", is_active=True),
                ContentTask(
                    id=task_id,
                    user_id=user_id,
                    intent_id=intent_id,
                    platform_id=platform_id,
                    status="PENDING",
                    task_type="video",
                    hook_text="旧任务",
                    storyboard=[{"shot": 1, "description": "测试", "duration": "3s"}],
                    script_text="旧任务文案",
                    title="旧任务标题",
                    comment_template="旧任务评论",
                    why_it_works="旧任务原因",
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                ),
            ]
        )
        await db.commit()

        new_task = await swap_task(task_id=task_id, db=db, current_user=user)

        assert new_task.id != task_id
        assert new_task.status == "PENDING"
        assert new_task.platform_name == "抖音"

    await engine.dispose()
