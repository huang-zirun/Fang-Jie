import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class MarketHotCreate(BaseModel):
    platform_id: uuid.UUID
    keyword: str
    hot_type: str
    analysis_result: dict | None = None
    recommended_structures: list | None = None
    priority_boost: float = 0.0
    expires_at: datetime | None = None


class MarketHotOut(BaseModel):
    id: uuid.UUID
    platform_id: uuid.UUID
    keyword: str
    hot_type: str
    analysis_result: dict | None
    recommended_structures: list | None
    priority_boost: float
    expires_at: datetime | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True, "extra": "ignore"}


class MarketHotUpdate(BaseModel):
    keyword: str | None = None
    hot_type: str | None = None
    analysis_result: dict | None = None
    recommended_structures: list | None = None
    priority_boost: float | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None


class ExtensionScrapeVideo(BaseModel):
    video_id: str = ""
    title: str = ""
    author: dict = {}
    statistics: dict = {}
    tags: list[str] = []
    created_at: str | None = None
    share_url: str = ""


class ExtensionScrapeData(BaseModel):
    keyword: str
    platform_id: uuid.UUID
    videos: list[ExtensionScrapeVideo]
    source: str = "extension_api"  # "extension_api" or "extension_ssr" or "extension_dom"


class XhsNoteItem(BaseModel):
    note_id: str
    title: str = ""
    author: dict[str, Any] = {}
    interact_info: dict[str, Any] = {}
    note_type: str = ""
    tag_list: list[str] = []
    desc: str = ""
    share_url: str = ""


class XhsExtensionScrapeData(BaseModel):
    keyword: str
    platform_id: uuid.UUID
    notes: list[XhsNoteItem]
    source: str = "api"  # intercepted / api / ssr / dom
