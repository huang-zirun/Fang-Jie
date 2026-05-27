import uuid
from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    intent_id: uuid.UUID
    platform_id: uuid.UUID
    task_type: str = "video"


class TaskNextCreate(BaseModel):
    platform_id: uuid.UUID | None = None
    task_type: str | None = None


class StoryboardShot(BaseModel):
    shot: int
    description: str
    duration: str | None = None
    label: str | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    intent_id: uuid.UUID
    platform_id: uuid.UUID
    platform_name: str = ""
    status: str = "PENDING"
    task_type: str = "video"
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
    deployed_at: datetime | None = None
    intent_name: str | None = None
    conversion_scripts: dict | None = None
    latest_snapshot: dict | None = None
    snapshot_count: int = 0

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
    deployed_at: datetime | None = None
    problem_type: str | None = None
    problem_desc: str | None = None
    play_count: int | None = None
    comment_count: int | None = None
    message_count: int | None = None
    snapshot_count: int = 0

    model_config = {"from_attributes": True}


class IntentDistributionItem(BaseModel):
    intent_name: str
    count: int


class ProblemStatsItem(BaseModel):
    problem_type: str
    count: int


class TaskOverviewOut(BaseModel):
    today_tasks: int
    today_published: int
    today_pending: int
    today_swapped: int
    total_problems: int
    intent_distribution: list[IntentDistributionItem]
    problem_stats: list[ProblemStatsItem]
