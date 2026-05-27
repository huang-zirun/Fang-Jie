import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ContentTask(Base):
    __tablename__ = "content_tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    intent_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("intents.id", ondelete="CASCADE"), nullable=False)
    platform_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False)
    structure_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("content_structures.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    task_type: Mapped[str] = mapped_column(String(10), nullable=False, default="video")
    hook_text: Mapped[str] = mapped_column(Text, nullable=False)
    storyboard: Mapped[dict] = mapped_column(JSON, nullable=False)
    script_text: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    comment_template: Mapped[str] = mapped_column(Text, nullable=False)
    why_it_works: Mapped[str] = mapped_column(Text, nullable=False)
    is_optimized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    optimization_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    swap_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prev_task_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("content_tasks.id", ondelete="SET NULL"), nullable=True)
    diagnosis_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("diagnosis_results.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="tasks")
    report = relationship("PerformanceReport", back_populates="task", uselist=False, lazy="selectin")
    diagnosis = relationship("DiagnosisResult", back_populates="task", uselist=False, lazy="selectin", foreign_keys=[diagnosis_id])
    snapshots = relationship("PerformanceSnapshot", back_populates="task", order_by="PerformanceSnapshot.snapshot_at", lazy="selectin")
