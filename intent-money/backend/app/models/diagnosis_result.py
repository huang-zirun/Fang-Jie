import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DiagnosisResult(Base):
    __tablename__ = "diagnosis_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("content_tasks.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    problem_type: Mapped[str] = mapped_column(String(30), nullable=False)
    problem_desc: Mapped[str] = mapped_column(String(200), nullable=False)
    optimization_direction: Mapped[str] = mapped_column(String(100), nullable=False)
    optimization_detail: Mapped[str] = mapped_column(Text, nullable=False)
    ai_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    snapshot_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    days_since_deploy: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    play_trend: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avg_daily_play_growth: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    diagnosed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("ContentTask", back_populates="diagnosis", foreign_keys="ContentTask.diagnosis_id")
