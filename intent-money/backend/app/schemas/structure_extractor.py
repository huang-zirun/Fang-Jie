import uuid
from datetime import datetime

from pydantic import BaseModel


class ExtractRequest(BaseModel):
    url: str
    platform: str


class ExtractResponse(BaseModel):
    id: uuid.UUID
    source_url: str
    platform_id: uuid.UUID
    hook_type: str
    emotion_structure: dict
    conversion_structure: dict
    key_elements: list
    viral_score: int
    analysis_summary: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
