import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    structures = relationship("ContentStructure", back_populates="platform", lazy="selectin")
    market_hots = relationship("MarketHot", back_populates="platform")
