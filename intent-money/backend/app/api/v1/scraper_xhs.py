from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_or_none
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.per_user_scraper import create_scraper_for_user
from app.services.platform_scraper.xhs_scraper import XhsScraper
from app.services.rate_limiter import rate_limiter

router = APIRouter(prefix="/xhs", tags=["scraper-xhs"])

_scraper = XhsScraper()


@router.post("/search")
async def search_xhs_notes(
    keyword: str,
    limit: int = 20,
    current_user: User | None = Depends(get_current_user_or_none),
    db: AsyncSession = Depends(get_db),
):
    if not keyword.strip():
        raise HTTPException(status_code=400, detail="keyword is required")

    if current_user and settings.PER_USER_SCRAPING:
        if not await rate_limiter.check(str(current_user.id), "xhs"):
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    scraper = None
    if current_user and settings.PER_USER_SCRAPING:
        scraper = await create_scraper_for_user(db, "xhs", str(current_user.id))
        if not scraper:
            raise HTTPException(status_code=403, detail="请先绑定小红书账号")
    else:
        scraper = _scraper

    try:
        results = await scraper.search_hot_notes(keyword=keyword, limit=limit)
    except Exception:
        if current_user and settings.PER_USER_SCRAPING:
            from app.services.per_user_scraper import mark_cookie_expired_on_failure
            await mark_cookie_expired_on_failure(db, "xhs", str(current_user.id))
            raise HTTPException(status_code=403, detail="Cookie 已过期，请重新绑定账号")
        raise
    return {"keyword": keyword, "count": len(results), "notes": results}


@router.post("/comments/{note_id}")
async def get_xhs_comments(
    note_id: str,
    limit: int = 50,
    current_user: User | None = Depends(get_current_user_or_none),
    db: AsyncSession = Depends(get_db),
):
    if not note_id.strip():
        raise HTTPException(status_code=400, detail="note_id is required")

    scraper = None
    if current_user and settings.PER_USER_SCRAPING:
        scraper = await create_scraper_for_user(db, "xhs", str(current_user.id))
        if not scraper:
            raise HTTPException(status_code=403, detail="请先绑定小红书账号")
    else:
        scraper = _scraper

    try:
        comments = await scraper.get_note_comments(note_id=note_id, limit=limit)
    except Exception:
        if current_user and settings.PER_USER_SCRAPING:
            from app.services.per_user_scraper import mark_cookie_expired_on_failure
            await mark_cookie_expired_on_failure(db, "xhs", str(current_user.id))
            raise HTTPException(status_code=403, detail="Cookie 已过期，请重新绑定账号")
        raise
    return {"note_id": note_id, "count": len(comments), "comments": comments}
