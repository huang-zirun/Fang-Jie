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
    status: str = "PENDING"
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
    published_at: datetime | None = None
    intent_name: str | None = None
    conversion_scripts: dict | None = None

    model_config = {"from_attributes": True}


class TaskHistoryOut(BaseModel):
    id: uuid.UUID
    intent_name: str = ""
    platform_name: str = ""
    status: str
    task_type: str = "video"
    hook_text: str = ""
    title: str = ""
    created_at: datetime
    published_at: datetime | None = None
    problem_type: str | None = None
    problem_desc: str | None = None
    play_count: int | None = None
    comment_count: int | None = None
    message_count: int | None = None

    model_config = {"from_attributes": True}
