from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.intent import Intent
from app.models.platform import Platform
from app.schemas.intent import IntentOut

router = APIRouter(prefix="/intents", tags=["intents"])
platforms_router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("", response_model=list[IntentOut])
async def get_intents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Intent).order_by(Intent.sort_order))
    return result.scalars().all()


@platforms_router.get("")
async def get_platforms(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Platform).where(Platform.is_active.is_(True))
    )
    platforms = result.scalars().all()
    return {
        "platforms": [
            {"id": str(p.id), "name": p.name, "description": p.description or "", "is_active": p.is_active}
            for p in platforms
        ]
    }
