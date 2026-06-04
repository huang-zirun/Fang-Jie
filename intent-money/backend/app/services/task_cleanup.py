import logging
from datetime import timedelta

from sqlalchemy import update

from app.database import async_session_factory
from app.models.content_task import ContentTask
from app.utils.time import utc_now_naive

logger = logging.getLogger(__name__)


async def expire_old_tasks():
    now = utc_now_naive()
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
            logger.info(f"已过期{expired_count}个超过48小时的任务")

        return expired_count
