import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import AnonymousRegisterResponse
from app.services.auth_service import create_anonymous_user
from app.utils.security import create_access_token, verify_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/anonymous", response_model=AnonymousRegisterResponse)
async def anonymous_register(db: AsyncSession = Depends(get_db)):
    user, token = await create_anonymous_user(db)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    return AnonymousRegisterResponse(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )


@router.post("/login", response_model=AnonymousRegisterResponse)
async def login(phone: str, code: str, db: AsyncSession = Depends(get_db)):
    if code != "123456":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code",
        )
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalars().first()
    if not user:
        user = User(phone=phone, is_anonymous=False)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    return AnonymousRegisterResponse(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )
