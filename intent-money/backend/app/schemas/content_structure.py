import uuid
from datetime import datetime

from pydantic import BaseModel


class ContentStructureCreate(BaseModel):
    intent_id: uuid.UUID
    platform_id: uuid.UUID
    hook_type: str
    emotion_structure: dict
    conversion_structure: dict
    prompt_template: str
    fallback_content: dict
    priority: int = 0


class ContentStructureOut(BaseModel):
    id: uuid.UUID
    intent_id: uuid.UUID
    platform_id: uuid.UUID
    hook_type: str
    emotion_structure: dict
    conversion_structure: dict
    prompt_template: str
    fallback_content: dict
    priority: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentStructureUpdate(BaseModel):
    hook_type: str | None = None
    emotion_structure: dict | None = None
    conversion_structure: dict | None = None
    prompt_template: str | None = None
    fallback_content: dict | None = None
    priority: int | None = None
    is_active: bool | None = None
