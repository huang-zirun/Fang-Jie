import uuid
from datetime import datetime

from pydantic import BaseModel


class AccountOut(BaseModel):
    id: uuid.UUID
    platform: str
    platform_user_id: str | None = None
    platform_nickname: str | None = None
    platform_avatar: str | None = None
    cookie_status: str
    cookie_set_at: datetime | None = None
    cookie_expires_at: datetime | None = None
    last_validated_at: datetime | None = None
    bind_status: str
    bind_method: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True, "extra": "ignore"}


class CookieImportRequest(BaseModel):
    cookie_data: str


class ExtensionCookieRequest(BaseModel):
    cookies: list[dict]


class QrCodeResponse(BaseModel):
    login_session_id: str
    qr_code_url: str
    expires_at: datetime | None = None


class QrCodeStatusResponse(BaseModel):
    status: str
    message: str | None = None
    account: AccountOut | None = None
