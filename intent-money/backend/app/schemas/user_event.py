from pydantic import BaseModel


class UserEventCreate(BaseModel):
    event_type: str
    page: str | None = None
    duration: float | None = None
    metadata_json: dict | None = None


class UserEventBatchCreate(BaseModel):
    session_id: str | None = None
    events: list[UserEventCreate]
