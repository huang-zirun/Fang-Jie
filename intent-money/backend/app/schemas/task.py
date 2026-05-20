import uuid
from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    intent_id: uuid.UUID
    platform_id: uuid.UUID
    task_type: str = "video"


class StoryboardShot(BaseModel):
    shot: int
    description: str
    duration: str | None = None
    label: str | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    platform_name: str = ""
    hook_text: str
    storyboard: list[StoryboardShot]
    script_text: str
    title: str
    comment_template: str
    why_it_works: str
    is_optimized: bool = False
    optimization_note: str | None = None
    prev_task_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
