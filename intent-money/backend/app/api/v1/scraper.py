import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_or_none
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.per_user_scraper import create_scraper_for_user
from app.services.platform_scraper.douyin_scraper import douyin_scraper
from app.services.platform_scraper.xhs_scraper import XhsScraper
from app.services.rate_limiter import rate_limiter
from app.api.v1.scraper_xhs import router as xhs_router

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraper", tags=["scraper"])
router.include_router(xhs_router)

_xhs_scraper = XhsScraper()
_douyin_scraper = douyin_scraper


@router.post("/douyin/search")
async def search_douyin_videos(
    keyword: str,
    limit: int = 20,
    current_user: User | None = Depends(get_current_user_or_none),
    db: AsyncSession = Depends(get_db),
):
    if not settings.SCRAPER_ENABLED:
        raise HTTPException(status_code=503, detail="Scraper service is disabled")
    if not keyword.strip():
        raise HTTPException(status_code=400, detail="keyword is required")

    if current_user and settings.PER_USER_SCRAPING:
        if not await rate_limiter.check(str(current_user.id), "douyin"):
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    scraper = None
    if current_user and settings.PER_USER_SCRAPING:
        scraper = await create_scraper_for_user(db, "douyin", str(current_user.id))
        if not scraper:
            raise HTTPException(status_code=403, detail="请先绑定抖音账号")
    else:
        scraper = _douyin_scraper

    try:
        results = await scraper.search_hot_videos(keyword=keyword, limit=limit)
    except Exception:
        if current_user and settings.PER_USER_SCRAPING:
            from app.services.per_user_scraper import mark_cookie_expired_on_failure
            await mark_cookie_expired_on_failure(db, "douyin", str(current_user.id))
            raise HTTPException(status_code=403, detail="Cookie 已过期，请重新绑定账号")
        raise
    return {"keyword": keyword, "count": len(results), "videos": results}


@router.post("/douyin/comments/{video_id}")
async def get_douyin_comments(
    video_id: str,
    limit: int = 50,
    current_user: User | None = Depends(get_current_user_or_none),
    db: AsyncSession = Depends(get_db),
):
    if not settings.SCRAPER_ENABLED:
        raise HTTPException(status_code=503, detail="Scraper service is disabled")
    if not video_id.strip():
        raise HTTPException(status_code=400, detail="video_id is required")

    scraper = None
    if current_user and settings.PER_USER_SCRAPING:
        scraper = await create_scraper_for_user(db, "douyin", str(current_user.id))
        if not scraper:
            raise HTTPException(status_code=403, detail="请先绑定抖音账号")
    else:
        scraper = _douyin_scraper

    try:
        comments = await scraper.get_video_comments(video_id=video_id, limit=limit)
    except Exception:
        if current_user and settings.PER_USER_SCRAPING:
            from app.services.per_user_scraper import mark_cookie_expired_on_failure
            await mark_cookie_expired_on_failure(db, "douyin", str(current_user.id))
            raise HTTPException(status_code=403, detail="Cookie 已过期，请重新绑定账号")
        raise
    return {"video_id": video_id, "count": len(comments), "comments": comments}


@router.get("/health")
async def check_scraper_health():
    douyin_ok = await _douyin_scraper.check_health()
    xhs_ok = await _xhs_scraper.check_health()
    return {
        "douyin": {"healthy": douyin_ok, "enabled": settings.SCRAPER_ENABLED},
        "xhs": {"healthy": xhs_ok, "enabled": settings.SCRAPER_ENABLED},
    }
