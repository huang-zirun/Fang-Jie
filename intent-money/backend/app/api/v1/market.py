import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.market_hot import MarketHot
from app.schemas.market_hot import ExtensionScrapeData, MarketHotCreate, MarketHotOut, XhsExtensionScrapeData
from app.services.market_service import analyze_market_trend, update_market_scores

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/hots", response_model=list[MarketHotOut])
async def list_hots(
    platform_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    query = select(MarketHot).where(
        MarketHot.is_active.is_(True),
        (MarketHot.expires_at.is_(None)) | (MarketHot.expires_at > now),
    )
    if platform_id:
        query = query.where(MarketHot.platform_id == platform_id)
    query = query.order_by(MarketHot.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/hots", response_model=MarketHotOut, status_code=status.HTTP_201_CREATED)
async def create_hot(
    data: MarketHotCreate,
    db: AsyncSession = Depends(get_db),
):
    hot = MarketHot(**data.model_dump(), is_active=True)
    db.add(hot)
    await db.commit()
    await db.refresh(hot)
    return hot


@router.post("/analyze")
async def analyze_market(
    platform_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await analyze_market_trend(db, platform_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return result


@router.delete("/hots/{hot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hot(
    hot_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MarketHot).where(MarketHot.id == hot_id))
    hot = result.scalars().first()
    if not hot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market hot not found")
    await db.delete(hot)
    await db.commit()


@router.post("/update-scores")
async def update_scores(
    db: AsyncSession = Depends(get_db),
):
    count = await update_market_scores(db)
    return {"updated_count": count}


@router.post("/extension-scrape", status_code=status.HTTP_201_CREATED)
async def receive_extension_scrape(
    data: ExtensionScrapeData,
    db: AsyncSession = Depends(get_db),
):
    """接收浏览器扩展提交的市场热门数据"""
    if not data.keyword.strip():
        raise HTTPException(status_code=400, detail="keyword is required")
    if not data.videos:
        raise HTTPException(status_code=400, detail="videos list is empty")

    saved_count = 0
    for video in data.videos:
        try:
            stats = video.statistics
            play_count = stats.get("play_count", 0)
            digg_count = stats.get("digg_count", 0)
            comment_count = stats.get("comment_count", 0)
            share_count = stats.get("share_count", 0)

            total_engagement = digg_count + comment_count + share_count
            priority_boost = min(total_engagement / 10000.0, 100.0) if play_count > 0 else 0.0

            hot = MarketHot(
                platform_id=data.platform_id,
                keyword=data.keyword,
                hot_type="extension_scraped",
                analysis_result={
                    "video_id": video.video_id,
                    "title": video.title,
                    "author": video.author,
                    "statistics": stats,
                    "tags": video.tags,
                    "created_at": video.created_at,
                    "share_url": video.share_url,
                    "source": data.source,
                },
                recommended_structures=video.tags if video.tags else None,
                priority_boost=priority_boost,
                is_active=True,
            )
            db.add(hot)
            saved_count += 1
        except Exception as e:
            logger.error(f"保存扩展抓取视频失败: {e}")
            continue

    try:
        await db.commit()
    except Exception as e:
        logger.error(f"提交扩展抓取数据失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save data")

    return {"keyword": data.keyword, "saved_count": saved_count, "source": data.source}


@router.post("/trigger-extension-scrape")
async def trigger_extension_scrape(
    keyword: str = "袜子",
    platform_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """触发扩展抓取 - 前端调用此端点后，应通知浏览器扩展执行抓取。

    扩展抓取结果通过 POST /market/extension-scrape 端点提交。
    此端点仅返回提示信息，实际抓取由扩展异步完成。
    """
    if not platform_id:
        from app.seed import PLATFORM_ID_DOUYIN
        platform_id = PLATFORM_ID_DOUYIN

    return {
        "message": "请在浏览器扩展中执行抓取",
        "keyword": keyword,
        "platform_id": str(platform_id),
        "extension_endpoint": "/market/extension-scrape",
        "instructions": {
            "step1": "前端通过 postMessage 通知扩展执行 SCRAPE_DOUYIN_SEARCH",
            "step2": "扩展在浏览器中抓取数据",
            "step3": "扩展通过 POST /market/extension-scrape 提交结果",
        }
    }


@router.post("/extension-scrape-xhs", status_code=status.HTTP_201_CREATED)
async def receive_xhs_extension_scrape(
    data: XhsExtensionScrapeData,
    db: AsyncSession = Depends(get_db),
):
    """接收浏览器扩展提交的小红书市场热门数据"""
    if not data.keyword.strip():
        raise HTTPException(status_code=400, detail="keyword is required")
    if not data.notes:
        raise HTTPException(status_code=400, detail="notes list is empty")

    saved_count = 0
    for note in data.notes:
        try:
            interact = note.interact_info
            liked_count = int(interact.get("liked_count", "0") or 0)
            collected_count = int(interact.get("collected_count", "0") or 0)
            comment_count = int(interact.get("comment_count", "0") or 0)
            share_count = int(interact.get("share_count", "0") or 0)

            total_engagement = liked_count + collected_count + comment_count + share_count
            priority_boost = min(total_engagement / 1000.0, 100.0)

            hot = MarketHot(
                platform_id=data.platform_id,
                keyword=data.keyword,
                hot_type="xhs_extension_intercepted" if data.source == "intercepted" else "xhs_extension_scraped",
                analysis_result={
                    "note_id": note.note_id,
                    "title": note.title,
                    "author": note.author,
                    "interact_info": interact,
                    "note_type": note.note_type,
                    "tag_list": note.tag_list,
                    "desc": note.desc,
                    "share_url": note.share_url,
                    "source": data.source,
                },
                recommended_structures=note.tag_list if note.tag_list else None,
                priority_boost=priority_boost,
                is_active=True,
            )
            db.add(hot)
            saved_count += 1
        except Exception as e:
            logger.error(f"保存小红书扩展抓取笔记失败: {e}")
            continue

    try:
        await db.commit()
    except Exception as e:
        logger.error(f"提交小红书扩展抓取数据失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save data")

    return {"keyword": data.keyword, "saved_count": saved_count, "source": data.source}
