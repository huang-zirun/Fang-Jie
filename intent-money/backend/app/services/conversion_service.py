import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversion_path import ConversionPath


async def get_conversion_scripts(db: AsyncSession, intent_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(ConversionPath)
        .where(
            ConversionPath.intent_id == intent_id,
            ConversionPath.is_active.is_(True),
        )
        .order_by(ConversionPath.sort_order.asc(), ConversionPath.created_at.asc())
    )
    paths = result.scalars().all()

    grouped: dict[str, list[dict]] = {
        "public_to_private": [],
        "private_to_deal": [],
        "deal_boost": [],
    }
    for path in paths:
        if path.stage in grouped:
            grouped[path.stage].append({
                "title": path.title,
                "scripts": path.scripts,
            })
    return grouped
