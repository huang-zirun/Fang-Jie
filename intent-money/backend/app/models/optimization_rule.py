import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OptimizationRule(Base):
    __tablename__ = "optimization_rules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    problem_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    condition_expr: Mapped[dict] = mapped_column(JSON, nullable=False)
    optimization_direction: Mapped[str] = mapped_column(String(100), nullable=False)
    optimization_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
