import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import update

from app.database import async_session_factory
from app.models.content_task import ContentTask

logger = logging.getLogger(__name__)


async def expire_old_tasks():
    now = datetime.now(timezone.utc)
    cutoff_48h = now - timedelta(hours=48)

    async with async_session_factory() as db:
        result = await db.execute(
            update(ContentTask)
            .where(
                ContentTask.status == "PUBLISHED",
                ContentTask.published_at < cutoff_48h,
            )
            .values(status="EXPIRED")
        )
        expired_count = result.rowcount
        await db.commit()

        if expired_count > 0:
            logger.info(f"Expired {expired_count} tasks older than 48h")

        return expired_count
