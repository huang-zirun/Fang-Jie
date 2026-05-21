import uuid
from datetime import datetime

from pydantic import BaseModel


class MarketHotCreate(BaseModel):
    platform_id: uuid.UUID
    keyword: str
    hot_type: str
    analysis_result: dict | None = None
    recommended_structures: list | None = None
    priority_boost: float = 0.0
    expires_at: datetime | None = None


class MarketHotOut(BaseModel):
    id: uuid.UUID
    platform_id: uuid.UUID
    keyword: str
    hot_type: str
    analysis_result: dict | None
    recommended_structures: list | None
    priority_boost: float
    expires_at: datetime | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MarketHotUpdate(BaseModel):
    keyword: str | None = None
    hot_type: str | None = None
    analysis_result: dict | None = None
    recommended_structures: list | None = None
    priority_boost: float | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None
