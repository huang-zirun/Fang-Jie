from fastapi import APIRouter, HTTPException

from app.config import settings
from app.services.platform_scraper.cdp_douyin_scraper import CdpDouyinScraper
from app.services.platform_scraper.cdp_xhs_scraper import CdpXhsScraper
from app.services.platform_scraper.douyin_scraper import douyin_scraper
from app.services.platform_scraper.xhs_scraper import XhsScraper
from app.api.v1.scraper_xhs import router as xhs_router

router = APIRouter(prefix="/scraper", tags=["scraper"])
router.include_router(xhs_router)

_xhs_scraper = CdpXhsScraper() if settings.CDP_ENABLED else XhsScraper()
_douyin_scraper = CdpDouyinScraper() if settings.CDP_ENABLED else douyin_scraper


@router.post("/douyin/search")
async def search_douyin_videos(keyword: str, limit: int = 20):
    if not settings.SCRAPER_ENABLED:
        raise HTTPException(status_code=503, detail="Scraper service is disabled")
    if not keyword.strip():
        raise HTTPException(status_code=400, detail="keyword is required")
    results = await _douyin_scraper.search_hot_videos(keyword=keyword, limit=limit)
    return {"keyword": keyword, "count": len(results), "videos": results}


@router.post("/douyin/comments/{video_id}")
async def get_douyin_comments(video_id: str, limit: int = 50):
    if not settings.SCRAPER_ENABLED:
        raise HTTPException(status_code=503, detail="Scraper service is disabled")
    if not video_id.strip():
        raise HTTPException(status_code=400, detail="video_id is required")
    comments = await _douyin_scraper.get_video_comments(video_id=video_id, limit=limit)
    return {"video_id": video_id, "count": len(comments), "comments": comments}


@router.get("/health")
async def check_scraper_health():
    douyin_ok = await _douyin_scraper.check_health()
    xhs_ok = await _xhs_scraper.check_health()
    cdp_mode = settings.CDP_ENABLED
    return {
        "douyin": {"healthy": douyin_ok, "enabled": settings.SCRAPER_ENABLED, "cdp": cdp_mode},
        "xhs": {"healthy": xhs_ok, "enabled": settings.SCRAPER_ENABLED, "cdp": cdp_mode},
    }
