from fastapi import APIRouter, HTTPException

from app.config import settings
from app.services.platform_scraper.cdp_xhs_scraper import CdpXhsScraper
from app.services.platform_scraper.xhs_scraper import XhsScraper

router = APIRouter(prefix="/xhs", tags=["scraper-xhs"])

_scraper = CdpXhsScraper() if settings.CDP_ENABLED else XhsScraper()


@router.post("/search")
async def search_xhs_notes(keyword: str, limit: int = 20):
    if not keyword.strip():
        raise HTTPException(status_code=400, detail="keyword is required")
    results = await _scraper.search_hot_notes(keyword=keyword, limit=limit)
    return {"keyword": keyword, "count": len(results), "notes": results}


@router.post("/comments/{note_id}")
async def get_xhs_comments(note_id: str, limit: int = 50):
    if not note_id.strip():
        raise HTTPException(status_code=400, detail="note_id is required")
    comments = await _scraper.get_note_comments(note_id=note_id, limit=limit)
    return {"note_id": note_id, "count": len(comments), "comments": comments}
