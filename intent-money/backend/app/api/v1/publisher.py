import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.content_task import ContentTask
from app.models.platform import Platform
from app.models.user import User
from app.schemas.publisher import (
    CookieStatusResponse,
    CookieUploadRequest,
    PublishResponse,
)
from app.services.auto_publisher import auto_publish_task
from app.services.cookie_manager import (
    get_cookie_expires_at,
    get_cookie_path,
    is_cookie_valid,
    save_cookie,
)
from app.utils.time import utc_now_naive

router = APIRouter(prefix="/publish", tags=["publish"])

PLATFORM_MAP = {
    "抖音": "douyin",
    "小红书": "xhs",
    "douyin": "douyin",
    "xhs": "xhs",
}


def _resolve_platform_key(platform_name: str) -> str | None:
    return PLATFORM_MAP.get(platform_name)


@router.post("/{task_id}/auto", response_model=PublishResponse)
async def auto_publish_endpoint(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ContentTask).where(ContentTask.id == task_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your task")
    if task.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task status incorrect")

    platform_result = await db.execute(
        Platform.__table__.select().where(Platform.id == task.platform_id)
    )
    platform_row = platform_result.first()
    if not platform_row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Platform not found")

    platform_key = _resolve_platform_key(platform_row.name)
    if not platform_key:
        return PublishResponse(
            success=False,
            task_id=str(task_id),
            error=f"不支持自动发布到平台: {platform_row.name}",
            fallback_to_manual=True,
        )

    if not settings.AUTO_PUBLISH_ENABLED:
        return PublishResponse(
            success=False,
            task_id=str(task_id),
            error="自动发布功能未启用，请手动发布",
            fallback_to_manual=True,
        )

    tags = [t.strip() for t in task.title.split("#") if t.strip()] if "#" in task.title else []

    pub_result = await auto_publish_task(
        platform=platform_key,
        user_id=str(current_user.id),
        title=task.title,
        content=task.script_text,
        tags=tags,
    )

    if pub_result["success"]:
        from sqlalchemy import update

        await db.execute(
            update(ContentTask)
            .where(ContentTask.id == task_id)
            .values(status="PUBLISHED", published_at=utc_now_naive())
        )
        await db.commit()

    return PublishResponse(
        success=pub_result["success"],
        task_id=str(task_id),
        error=pub_result.get("error"),
        fallback_to_manual=not pub_result["success"],
    )


@router.post("/cookie", response_model=dict)
async def upload_cookie(
    data: CookieUploadRequest,
    current_user: User = Depends(get_current_user),
):
    if data.platform not in ("douyin", "xhs"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="平台仅支持 douyin / xhs")

    path = await save_cookie(data.platform, str(current_user.id), data.cookie_data)
    return {"message": "Cookie 已保存", "path": path}


@router.get("/cookie/{platform}", response_model=CookieStatusResponse)
async def check_cookie_status(
    platform: str,
    current_user: User = Depends(get_current_user),
):
    if platform not in ("douyin", "xhs"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="平台仅支持 douyin / xhs")

    user_id = str(current_user.id)
    has_cookie = (await get_cookie_path(platform, user_id)) is not None
    valid = await is_cookie_valid(platform, user_id) if has_cookie else False
    expires_at = await get_cookie_expires_at(platform, user_id) if has_cookie else None

    return CookieStatusResponse(
        platform=platform,
        has_cookie=has_cookie,
        is_valid=valid,
        expires_at=expires_at,
    )
