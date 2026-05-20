import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ContentStructure(Base):
    __tablename__ = "content_structures"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intent_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("intents.id", ondelete="CASCADE"), nullable=False, index=True)
    platform_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False, index=True)
    hook_type: Mapped[str] = mapped_column(String(30), nullable=False)
    emotion_structure: Mapped[dict] = mapped_column(JSON, nullable=False)
    conversion_structure: Mapped[dict] = mapped_column(JSON, nullable=False)
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    fallback_content: Mapped[dict] = mapped_column(JSON, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    intent = relationship("Intent", back_populates="structures")
    platform = relationship("Platform", back_populates="structures")
