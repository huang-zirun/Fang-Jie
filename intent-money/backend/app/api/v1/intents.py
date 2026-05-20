from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.intent import Intent
from app.schemas.intent import IntentOut

router = APIRouter(prefix="/intents", tags=["intents"])


@router.get("", response_model=list[IntentOut])
async def get_intents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Intent).order_by(Intent.sort_order))
    return result.scalars().all()
