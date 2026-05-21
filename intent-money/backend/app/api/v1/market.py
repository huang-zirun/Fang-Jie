import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.market_hot import MarketHot
from app.schemas.market_hot import MarketHotCreate, MarketHotOut
from app.services.market_service import analyze_market_trend, update_market_scores

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
