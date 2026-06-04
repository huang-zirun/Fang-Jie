import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.services.cookie_vault import cookie_vault

logger = logging.getLogger(__name__)


async def validate_all_cookies(db) -> int:
    from app.models.user_platform_account import UserPlatformAccount

    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.cookie_status == "active"
        )
    )
    accounts = result.scalars().all()
    validated = 0
    for account in accounts:
        is_valid = await _validate_account_cookie(account)
        now = datetime.now(timezone.utc)
        account.last_validated_at = now
        if not is_valid:
            account.cookie_status = "expired"
            logger.info(f"Cookie已过期: {account.platform} 用户{account.user_id}")
        validated += 1
    await db.commit()
    logger.info(f"校验{validated}个Cookie，已标记过期")
    return validated


async def _validate_account_cookie(account) -> bool:
    if not account.encrypted_cookie or not account.cookie_iv:
        return False
    try:
        cookie_str = cookie_vault.decrypt(
            account.encrypted_cookie, account.cookie_iv, str(account.user_id)
        )
    except Exception:
        return False
    return await _check_platform_login(account.platform, cookie_str)


async def validate_platform_cookie(platform: str, cookie_data: str) -> bool:
    if platform == "xhs":
        from app.services.xhs_cookie_validator import validate_xhs_cookie
        return await validate_xhs_cookie(cookie_data)

    if platform == "douyin":
        from app.services.douyin_cookie_validator import validate_douyin_cookie
        return await validate_douyin_cookie(cookie_data)

    logger.warning(f"不支持的平台校验: {platform}")
    return False


async def _check_platform_login(platform: str, cookie_str: str) -> bool:
    return await validate_platform_cookie(platform, cookie_str)


async def mark_cookie_expired(db, user_id: str, platform: str) -> None:
    from app.models.user_platform_account import UserPlatformAccount

    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == user_id,
            UserPlatformAccount.platform == platform,
        )
    )
    account = result.scalars().first()
    if account:
        account.cookie_status = "expired"
        await db.commit()
        logger.info(f"Cookie已标记过期: {platform}_{user_id}")


async def get_expiring_cookies(db, days: int = 2) -> list:
    from app.models.user_platform_account import UserPlatformAccount

    threshold = datetime.now(timezone.utc) + timedelta(days=days)
    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.cookie_status == "active",
            UserPlatformAccount.cookie_expires_at <= threshold,
        )
    )
    return result.scalars().all()
