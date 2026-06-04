import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user_platform_account import UserPlatformAccount
from app.services.cookie_vault import cookie_vault
from app.services.platform_scraper.base_scraper import BasePlatformScraper

logger = logging.getLogger(__name__)


async def create_scraper_for_user(
    db: AsyncSession,
    platform: str,
    user_id: str,
) -> BasePlatformScraper | None:
    if not settings.PER_USER_SCRAPING:
        return _create_shared_scraper(platform)

    # 将字符串转换为 UUID
    try:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    except (ValueError, AttributeError):
        logger.error(f"无效用户ID格式: {user_id}")
        return None

    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == user_uuid,
            UserPlatformAccount.platform == platform,
        )
    )
    account = result.scalars().first()

    if not account or account.cookie_status != "active" or not account.encrypted_cookie or not account.cookie_iv:
        return None

    try:
        cookie_str = cookie_vault.decrypt(account.encrypted_cookie, account.cookie_iv, user_id)
    except Exception as e:
        logger.error(f"Cookie解密失败({platform}_{user_id}): {e}")
        return None

    account.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    return _create_scraper_with_cookie(platform, cookie_str)


def _create_shared_scraper(platform: str) -> BasePlatformScraper:
    if platform == "xhs":
        from app.services.platform_scraper.xhs_scraper import XhsScraper
        return XhsScraper()
    elif platform == "douyin":
        from app.services.platform_scraper.douyin_scraper import DouyinScraper
        return DouyinScraper()
    raise ValueError(f"Unsupported platform: {platform}")


def _create_scraper_with_cookie(platform: str, cookie_str: str) -> BasePlatformScraper:
    if platform == "xhs":
        from app.services.platform_scraper.xhs_scraper import XhsScraper
        xhs = XhsScraper()
        xhs._cookie = cookie_str
        return xhs
    elif platform == "douyin":
        from app.services.platform_scraper.douyin_scraper import DouyinScraper
        dy = DouyinScraper()
        dy._headers["Cookie"] = cookie_str
        return dy
    raise ValueError(f"Unsupported platform: {platform}")


async def mark_cookie_expired_on_failure(db: AsyncSession, platform: str, user_id: str) -> None:
    # 将字符串转换为 UUID
    try:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    except (ValueError, AttributeError):
        logger.error(f"无效用户ID格式: {user_id}")
        return

    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == user_uuid,
            UserPlatformAccount.platform == platform,
        )
    )
    account = result.scalars().first()
    if account:
        account.cookie_status = "expired"
        await db.commit()
        logger.info(f"Cookie因401自动标记过期: {platform}_{user_id}")
