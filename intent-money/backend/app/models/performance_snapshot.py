import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PerformanceSnapshot(Base):
    __tablename__ = "performance_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("content_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    play_count: Mapped[int] = mapped_column(Integer, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("ContentTask", back_populates="snapshots")
