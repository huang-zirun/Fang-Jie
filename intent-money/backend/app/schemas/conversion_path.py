import uuid
from datetime import datetime

from pydantic import BaseModel


class ConversionPathCreate(BaseModel):
    intent_id: uuid.UUID
    stage: str
    title: str
    scripts: dict
    sort_order: int = 0
    is_active: bool = True


class ConversionPathOut(BaseModel):
    id: uuid.UUID
    intent_id: uuid.UUID
    stage: str
    title: str
    scripts: dict
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "extra": "ignore"}


class ConversionPathUpdate(BaseModel):
    stage: str | None = None
    title: str | None = None
    scripts: dict | None = None
    sort_order: int | None = None
    is_active: bool | None = None
