import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class SnapshotCreate(BaseModel):
    play_count: int
    comment_count: int
    message_count: int

    @field_validator("play_count", "comment_count", "message_count")
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v

    @field_validator("play_count")
    @classmethod
    def validate_play_count_max(cls, v: int) -> int:
        if v > 100000000:
            raise ValueError("Play count exceeds maximum")
        return v


class SnapshotOut(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    play_count: int
    comment_count: int
    message_count: int
    source: str = "manual"
    snapshot_at: datetime

    model_config = {"from_attributes": True}


class DeployDateUpdate(BaseModel):
    deployed_at: datetime | None = None


class SnapshotSummaryOut(BaseModel):
    total_snapshots: int
    days_since_deploy: int
    play_trend: str
    latest_play_count: int
    avg_daily_play_growth: float

    model_config = {"from_attributes": True}
