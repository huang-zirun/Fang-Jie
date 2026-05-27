from fastapi import APIRouter

from app.config import settings
from app.services.platform_scraper.cdp_browser import CdpBrowser

router = APIRouter(prefix="/cdp", tags=["cdp"])


@router.get("/health")
async def check_cdp_health():
    browser = CdpBrowser(
        host=settings.CDP_DEBUG_HOST,
        port=settings.CDP_DEBUG_PORT,
        scheme=settings.CDP_DEBUG_SCHEME,
    )
    cdp_available = await browser.check_health()
    return {
        "cdp_available": cdp_available,
        "host": settings.CDP_DEBUG_HOST,
        "port": settings.CDP_DEBUG_PORT,
        "scheme": settings.CDP_DEBUG_SCHEME,
    }
