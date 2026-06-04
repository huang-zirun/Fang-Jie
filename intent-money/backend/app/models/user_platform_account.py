import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserPlatformAccount(Base):
    __tablename__ = "user_platform_accounts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    platform_user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    platform_nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    platform_avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    encrypted_cookie: Mapped[str | None] = mapped_column(Text, nullable=True)
    cookie_iv: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cookie_status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", nullable=False)
    cookie_set_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cookie_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bind_status: Mapped[str] = mapped_column(String(20), default="unbound", server_default="unbound", nullable=False)
    bind_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    login_session_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    qr_code_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    login_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="platform_accounts")

    __table_args__ = (
        UniqueConstraint("user_id", "platform", name="uq_user_platform"),
        Index("ix_platform_cookie_status", "platform", "cookie_status"),
    )
