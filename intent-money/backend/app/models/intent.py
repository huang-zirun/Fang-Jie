import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Intent(Base):
    __tablename__ = "intents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    structures = relationship("ContentStructure", back_populates="intent", lazy="selectin")
    conversion_paths = relationship("ConversionPath", back_populates="intent")
