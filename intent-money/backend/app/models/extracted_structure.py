import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExtractedStructure(Base):
    __tablename__ = "extracted_structures"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    platform_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False, index=True)
    hook_type: Mapped[str] = mapped_column(String(50), nullable=False)
    emotion_structure: Mapped[dict] = mapped_column(JSON, nullable=False)
    conversion_structure: Mapped[dict] = mapped_column(JSON, nullable=False)
    key_elements: Mapped[list] = mapped_column(JSON, nullable=False)
    viral_score: Mapped[int] = mapped_column(Integer, nullable=False)
    analysis_summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    platform = relationship("Platform")
