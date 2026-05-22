from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.user_event import UserEvent
from app.schemas.user_event import UserEventBatchCreate

router = APIRouter(prefix="/events", tags=["events"])


@router.post("")
async def batch_create_events(
    data: UserEventBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    events = []
    for event_data in data.events:
        event = UserEvent(
            user_id=current_user.id,
            session_id=data.session_id,
            event_type=event_data.event_type,
            page=event_data.page,
            duration=event_data.duration,
            metadata_json=event_data.metadata_json,
        )
        events.append(event)
    db.add_all(events)
    await db.commit()
    return {"received": len(events)}


@router.get("/stats")
async def get_event_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_events = await db.scalar(select(func.count(UserEvent.id)))
    event_type_counts = await db.execute(
        select(UserEvent.event_type, func.count(UserEvent.id))
        .group_by(UserEvent.event_type)
    )
    type_stats = {row[0]: row[1] for row in event_type_counts.all()}

    total_users = await db.scalar(
        select(func.count(func.distinct(UserEvent.user_id)))
    )
    avg_duration = await db.scalar(
        select(func.avg(UserEvent.duration)).where(UserEvent.duration.isnot(None))
    )

    return {
        "total_events": total_events or 0,
        "total_users": total_users or 0,
        "avg_duration": round(avg_duration, 2) if avg_duration else None,
        "by_type": type_stats,
    }
