import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.security import create_access_token


async def create_anonymous_user(db: AsyncSession) -> tuple[User, str]:
    user = User(is_anonymous=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    return user, token
