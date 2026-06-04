import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.cookie_vault import cookie_vault

logger = logging.getLogger(__name__)


async def save_cookie(db: AsyncSession, platform: str, user_id: str, cookie_data: str) -> str:
    from app.models.user_platform_account import UserPlatformAccount

    encrypted, iv = cookie_vault.encrypt(cookie_data, user_id)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.COOKIE_EXPIRE_DAYS)
    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == user_id,
            UserPlatformAccount.platform == platform,
        )
    )
    account = result.scalars().first()
    if account:
        account.encrypted_cookie = encrypted
        account.cookie_iv = iv
        account.cookie_status = "active"
        account.cookie_set_at = now
        account.cookie_expires_at = expires_at
        account.last_validated_at = now
        account.bind_status = "bound"
    else:
        account = UserPlatformAccount(
            user_id=user_id,
            platform=platform,
            encrypted_cookie=encrypted,
            cookie_iv=iv,
            cookie_status="active",
            cookie_set_at=now,
            cookie_expires_at=expires_at,
            last_validated_at=now,
            bind_status="bound",
        )
        db.add(account)
    await db.commit()
    await db.refresh(account)
    logger.info(f"Cookie已保存: {platform}_{user_id}")
    return str(account.id)


async def get_cookie(db: AsyncSession, platform: str, user_id: str) -> str | None:
    from app.models.user_platform_account import UserPlatformAccount

    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == user_id,
            UserPlatformAccount.platform == platform,
        )
    )
    account = result.scalars().first()
    if not account or not account.encrypted_cookie or not account.cookie_iv:
        return None
    if account.cookie_status != "active":
        return None
    try:
        return cookie_vault.decrypt(account.encrypted_cookie, account.cookie_iv, user_id)
    except Exception as e:
        logger.error(f"Cookie解密失败: {e}")
        return None


async def is_cookie_valid(db: AsyncSession, platform: str, user_id: str) -> bool:
    from app.models.user_platform_account import UserPlatformAccount

    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == user_id,
            UserPlatformAccount.platform == platform,
        )
    )
    account = result.scalars().first()
    if not account:
        return False
    if account.cookie_status != "active":
        return False
    if account.cookie_expires_at and account.cookie_expires_at < datetime.now(timezone.utc):
        return False
    return True


async def get_cookie_expires_at(db: AsyncSession, platform: str, user_id: str) -> str | None:
    from app.models.user_platform_account import UserPlatformAccount

    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == user_id,
            UserPlatformAccount.platform == platform,
        )
    )
    account = result.scalars().first()
    if not account or not account.cookie_expires_at:
        return None
    return account.cookie_expires_at.isoformat()


async def get_cookie_path(db: AsyncSession, platform: str, user_id: str) -> str | None:
    from app.models.user_platform_account import UserPlatformAccount

    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == user_id,
            UserPlatformAccount.platform == platform,
        )
    )
    account = result.scalars().first()
    if not account or not account.encrypted_cookie or not account.cookie_iv:
        return None
    return str(account.id)


async def mark_cookie_expired(db: AsyncSession, platform: str, user_id: str) -> None:
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
