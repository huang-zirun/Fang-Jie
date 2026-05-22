from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import AnonymousRegisterResponse, SendCodeRequest
from app.services.auth_service import create_anonymous_user
from app.services.sms_service import send_verification_code, verify_code
from app.utils.security import create_access_token

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


@router.post("/send-code")
async def send_code(data: SendCodeRequest):
    await send_verification_code(data.phone)
    return {"message": "Verification code sent"}


@router.post("/login", response_model=AnonymousRegisterResponse)
async def login(phone: str, code: str, db: AsyncSession = Depends(get_db)):
    if not verify_code(phone, code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code",
        )
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalars().first()
    if not user:
        user = User(phone=phone, is_anonymous=False, role="user")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    return AnonymousRegisterResponse(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )


@router.post("/set-admin")
async def set_admin(
    phone: str,
    secret_key: str,
    db: AsyncSession = Depends(get_db),
):
    if secret_key != settings.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret key",
        )
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user.role = "admin"
    await db.commit()
    await db.refresh(user)
    return {"message": "Admin role set successfully", "user_id": str(user.id)}
