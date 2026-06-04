import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.user_platform_account import UserPlatformAccount
from app.schemas.account import AccountOut, CookieImportRequest, ExtensionCookieRequest, QrCodeResponse, QrCodeStatusResponse
from app.services.cookie_vault import cookie_vault

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/accounts", tags=["accounts"])

VALID_PLATFORMS = {"douyin", "xhs"}

# Chrome 扩展 API sameSite 值 → Playwright storage_state 值
_SAME_SITE_MAP = {
    "no_restriction": "None",
    "lax": "Lax",
    "strict": "Strict",
    "unspecified": "None",
}

# 平台名称别名：扩展使用全名，后端数据库使用缩写
_PLATFORM_ALIASES = {
    "xiaohongshu": "xhs",
}

# 平台父域名映射：用于将子域名 Cookie 规范化为父域名
_PLATFORM_DOMAINS = {
    "xhs": ".xiaohongshu.com",
    "douyin": ".douyin.com",
}


def _normalize_platform(platform: str) -> str:
    return _PLATFORM_ALIASES.get(platform, platform)


def _normalize_cookie_domain(domain: str, platform: str) -> str:
    """将 Cookie domain 规范化为平台父域名，确保跨子域可用。

    例如: www.xiaohongshu.com → .xiaohongshu.com
         creator.xiaohongshu.com → .xiaohongshu.com
         .xiaohongshu.com → .xiaohongshu.com (不变)
    """
    parent = _PLATFORM_DOMAINS.get(platform)
    if not parent:
        return domain
    # domain 可能以 . 开头（如 .xiaohongshu.com）或不以 . 开头（如 www.xiaohongshu.com）
    # 如果 domain 已经是父域名，直接返回
    if domain == parent or domain == parent.lstrip("."):
        return parent
    # 如果 domain 以父域名结尾（如 www.xiaohongshu.com 以 .xiaohongshu.com 结尾）
    if domain.endswith(parent) or domain.endswith(parent.lstrip(".")):
        return parent
    return domain


@router.get("/", response_model=list[AccountOut])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == current_user.id
        )
    )
    return result.scalars().all()


@router.post("/{platform}/cookie", response_model=AccountOut)
async def import_cookie(
    platform: str,
    data: CookieImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    platform = _normalize_platform(platform)
    if platform not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")

    is_valid = await _validate_cookie(platform, data.cookie_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Cookie 无效或已过期，请重新获取")

    encrypted, iv = cookie_vault.encrypt(data.cookie_data, str(current_user.id))
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.COOKIE_EXPIRE_DAYS)

    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == current_user.id,
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
        account.bind_method = "cookie_import"
    else:
        account = UserPlatformAccount(
            user_id=current_user.id,
            platform=platform,
            encrypted_cookie=encrypted,
            cookie_iv=iv,
            cookie_status="active",
            cookie_set_at=now,
            cookie_expires_at=expires_at,
            last_validated_at=now,
            bind_status="bound",
            bind_method="cookie_import",
        )
        db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.post("/{platform}/extension", response_model=AccountOut)
async def extension_cookie_login(
    platform: str,
    data: ExtensionCookieRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    platform = _normalize_platform(platform)
    if platform not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")

    converted_cookies = []
    for c in data.cookies:
        same_site_raw = c.get("sameSite", "unspecified").lower()
        converted = {
            "name": c["name"],
            "value": c["value"],
            "domain": _normalize_cookie_domain(c["domain"], platform),
            "path": c.get("path", "/"),
            "expires": c.get("expirationDate", -1),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False),
            "sameSite": _SAME_SITE_MAP.get(same_site_raw, "None"),
        }
        converted_cookies.append(converted)

    storage_state = {"cookies": converted_cookies, "origins": []}
    storage_state_json = json.dumps(storage_state)

    # 先保存 Cookie，后续在后台异步验证
    encrypted, iv = cookie_vault.encrypt(storage_state_json, str(current_user.id))
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.COOKIE_EXPIRE_DAYS)

    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == current_user.id,
            UserPlatformAccount.platform == platform,
        )
    )
    account = result.scalars().first()
    if account:
        account.encrypted_cookie = encrypted
        account.cookie_iv = iv
        account.cookie_status = "pending"
        account.cookie_set_at = now
        account.cookie_expires_at = expires_at
        account.last_validated_at = now
        account.bind_status = "bound"
        account.bind_method = "extension"
    else:
        account = UserPlatformAccount(
            user_id=current_user.id,
            platform=platform,
            encrypted_cookie=encrypted,
            cookie_iv=iv,
            cookie_status="pending",
            cookie_set_at=now,
            cookie_expires_at=expires_at,
            last_validated_at=now,
            bind_status="bound",
            bind_method="extension",
        )
        db.add(account)
    await db.commit()
    await db.refresh(account)
    
    # 启动后台验证任务（不阻塞响应）
    async def validate_in_background():
        """后台验证 Cookie 有效性并更新状态"""
        from app.database import async_session_factory
        async with async_session_factory() as bg_db:
            try:
                is_valid = await _validate_cookie(platform, storage_state_json)
                now_bg = datetime.now(timezone.utc)
                
                # 重新查询 account 以在新的 session 中操作
                bg_result = await bg_db.execute(
                    select(UserPlatformAccount).where(
                        UserPlatformAccount.user_id == current_user.id,
                        UserPlatformAccount.platform == platform,
                    )
                )
                bg_account = bg_result.scalars().first()
                if bg_account:
                    bg_account.last_validated_at = now_bg
                    if is_valid:
                        bg_account.cookie_status = "active"
                    else:
                        bg_account.cookie_status = "expired"
                    await bg_db.commit()
                    logger.info(f"后台验证完成: platform={platform}, user_id={current_user.id}, valid={is_valid}")
            except Exception as e:
                logger.error(f"后台验证失败: platform={platform}, user_id={current_user.id}, error={e}")
    
    asyncio.create_task(validate_in_background())
    
    return account


@router.post("/{platform}/validate")
async def validate_account(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    platform = _normalize_platform(platform)
    if platform not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")

    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == current_user.id,
            UserPlatformAccount.platform == platform,
        )
    )
    account = result.scalars().first()
    if not account or not account.encrypted_cookie or not account.cookie_iv:
        raise HTTPException(status_code=404, detail=f"未绑定{platform}账号")

    cookie_data = cookie_vault.decrypt(account.encrypted_cookie, account.cookie_iv, str(current_user.id))
    is_valid = await _validate_cookie(platform, cookie_data)

    now = datetime.now(timezone.utc)
    account.last_validated_at = now
    if is_valid:
        account.cookie_status = "active"
    else:
        account.cookie_status = "expired"
    await db.commit()

    return {"platform": platform, "valid": is_valid, "cookie_status": account.cookie_status}


@router.delete("/{platform}")
async def unbind_account(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    platform = _normalize_platform(platform)
    if platform not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")

    result = await db.execute(
        select(UserPlatformAccount).where(
            UserPlatformAccount.user_id == current_user.id,
            UserPlatformAccount.platform == platform,
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail=f"未绑定{platform}账号")

    await db.delete(account)
    await db.commit()
    return {"message": f"已解绑{platform}账号"}


@router.post("/{platform}/qrcode", response_model=QrCodeResponse)
async def request_qrcode(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    platform = _normalize_platform(platform)
    if platform not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")

    from app.services.qrcode_login import start_qr_login
    result = await start_qr_login(platform, str(current_user.id))

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "启动扫码登录失败"))

    return QrCodeResponse(
        login_session_id=result["login_session_id"],
        qr_code_url=result["qr_code_url"],
        expires_at=result.get("expires_at"),
    )


@router.get("/{platform}/qrcode/{session_id}/status", response_model=QrCodeStatusResponse)
async def check_qrcode_status(
    platform: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    platform = _normalize_platform(platform)

    from app.services.qrcode_login import check_login_status

    result = await check_login_status(session_id)

    account = None
    storage_state = result.pop("storage_state", None)
    if result["status"] == "confirmed" and storage_state:
        storage_state_json = json.dumps(storage_state)
        encrypted, iv = cookie_vault.encrypt(storage_state_json, str(current_user.id))
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.COOKIE_EXPIRE_DAYS)

        db_result = await db.execute(
            select(UserPlatformAccount).where(
                UserPlatformAccount.user_id == current_user.id,
                UserPlatformAccount.platform == platform,
            )
        )
        db_account = db_result.scalars().first()
        if db_account:
            db_account.encrypted_cookie = encrypted
            db_account.cookie_iv = iv
            db_account.cookie_status = "active"
            db_account.cookie_set_at = now
            db_account.cookie_expires_at = expires_at
            db_account.last_validated_at = now
            db_account.bind_status = "bound"
            db_account.bind_method = "qrcode"
        else:
            db_account = UserPlatformAccount(
                user_id=current_user.id,
                platform=platform,
                encrypted_cookie=encrypted,
                cookie_iv=iv,
                cookie_status="active",
                cookie_set_at=now,
                cookie_expires_at=expires_at,
                last_validated_at=now,
                bind_status="bound",
                bind_method="qrcode",
            )
            db.add(db_account)
        await db.commit()
        await db.refresh(db_account)
        account = db_account

    return QrCodeStatusResponse(
        status=result["status"],
        message=result.get("message"),
        account=account,
    )


async def _validate_cookie(platform: str, cookie_data: str) -> bool:
    from app.services.cookie_lifecycle import validate_platform_cookie
    return await validate_platform_cookie(platform, cookie_data)
