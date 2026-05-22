import uuid
from datetime import datetime

from pydantic import BaseModel


class AnonymousRegisterResponse(BaseModel):
    user_id: uuid.UUID
    token: str
    expires_at: datetime


class SendCodeRequest(BaseModel):
    phone: str
