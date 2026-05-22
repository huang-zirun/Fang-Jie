from pydantic import BaseModel


class AutoPublishRequest(BaseModel):
    task_id: str


class CookieUploadRequest(BaseModel):
    platform: str
    cookie_data: str


class PublishResponse(BaseModel):
    success: bool
    task_id: str
    error: str | None = None
    fallback_to_manual: bool = False


class CookieStatusResponse(BaseModel):
    platform: str
    has_cookie: bool
    is_valid: bool
    expires_at: str | None = None
