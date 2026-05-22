from abc import ABC, abstractmethod
from typing import Any


class BasePlatformScraper(ABC):
    @abstractmethod
    async def search_hot_videos(self, keyword: str, limit: int = 20) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_video_detail(self, video_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def get_video_comments(self, video_id: str, limit: int = 50) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def search_hot_notes(self, keyword: str, limit: int = 20) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_note_detail(self, note_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def get_note_comments(self, note_id: str, limit: int = 50) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def check_health(self) -> bool: ...
