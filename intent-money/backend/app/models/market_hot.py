import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MarketHot(Base):
    __tablename__ = "market_hots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword: Mapped[str] = mapped_column(String(100), nullable=False)
    hot_type: Mapped[str] = mapped_column(String(30), nullable=False)
    analysis_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommended_structures: Mapped[list | None] = mapped_column(JSON, nullable=True)
    priority_boost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    comment_sentiment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    platform = relationship("Platform", back_populates="market_hots")
