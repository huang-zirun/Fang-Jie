import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.services.platform_scraper.base_scraper import BasePlatformScraper

logger = logging.getLogger(__name__)


class DouyinScraper(BasePlatformScraper):
    def __init__(self) -> None:
        self._base_url = "https://www.douyin.com"
        self._api_url = "https://www.douyin.com/aweme/v1"
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json, text/plain, */*",
        }
        if settings.DOUYIN_COOKIE:
            self._headers["Cookie"] = settings.DOUYIN_COOKIE

    async def search_hot_videos(self, keyword: str, limit: int = 20) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=settings.SCRAPER_TIMEOUT, headers=self._headers) as client:
                params: dict[str, str | int] = {
                    "keyword": keyword,
                    "count": min(limit, 50),
                    "offset": 0,
                    "search_source": "normal_search",
                    "type": 1,
                }
                resp = await client.get(f"{self._api_url}/search/item/", params=params)
                resp.raise_for_status()
                data = resp.json()

            items = data.get("data", [])
            if not items and isinstance(data, dict):
                items = data.get("data", {}).get("list", [])

            results: list[dict[str, Any]] = []
            for item in items[:limit]:
                aweme_info = item.get("aweme_info", item)
                video = self._parse_video_item(aweme_info)
                if video:
                    results.append(video)

            return results
        except httpx.HTTPStatusError as e:
            logger.error(f"Douyin search HTTP error: {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Douyin search request error: {e}")
            return []
        except Exception as e:
            logger.error(f"Douyin search unexpected error: {e}")
            return []

    async def get_video_detail(self, video_id: str) -> dict[str, Any] | None:
        try:
            async with httpx.AsyncClient(timeout=settings.SCRAPER_TIMEOUT, headers=self._headers) as client:
                params: dict[str, str] = {"aweme_id": video_id}
                resp = await client.get(f"{self._api_url}/aweme/detail/", params=params)
                resp.raise_for_status()
                data = resp.json()

            aweme_detail = data.get("aweme_detail", data)
            return self._parse_video_item(aweme_detail)
        except httpx.HTTPStatusError as e:
            logger.error(f"Douyin video detail HTTP error: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Douyin video detail request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Douyin video detail unexpected error: {e}")
            return None

    async def get_video_comments(self, video_id: str, limit: int = 50) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=settings.SCRAPER_TIMEOUT, headers=self._headers) as client:
                params: dict[str, str | int] = {
                    "aweme_id": video_id,
                    "count": min(limit, 50),
                    "cursor": 0,
                }
                resp = await client.get(f"{self._api_url}/comment/list/", params=params)
                resp.raise_for_status()
                data = resp.json()

            comments_raw = data.get("comments", [])
            if not comments_raw:
                comments_raw = data.get("data", {}).get("comments", [])

            results: list[dict[str, Any]] = []
            for c in comments_raw[:limit]:
                comment = self._parse_comment_item(c)
                if comment:
                    results.append(comment)

            return results
        except httpx.HTTPStatusError as e:
            logger.error(f"Douyin comments HTTP error: {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Douyin comments request error: {e}")
            return []
        except Exception as e:
            logger.error(f"Douyin comments unexpected error: {e}")
            return []

    async def search_hot_notes(self, keyword: str, limit: int = 20) -> list[dict[str, Any]]:
        logger.warning("DouyinScraper does not support note search, returning empty list")
        return []

    async def get_note_detail(self, note_id: str) -> dict[str, Any] | None:
        logger.warning("DouyinScraper does not support note detail, returning None")
        return None

    async def get_note_comments(self, note_id: str, limit: int = 50) -> list[dict[str, Any]]:
        logger.warning("DouyinScraper does not support note comments, returning empty list")
        return []

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10, headers=self._headers) as client:
                resp = await client.get(self._base_url)
                return resp.status_code == 200
        except Exception:
            return False

    def _parse_video_item(self, item: dict[str, Any]) -> dict[str, Any] | None:
        try:
            if not item or not isinstance(item, dict):
                return None

            video_id = item.get("aweme_id", item.get("id", ""))
            desc = item.get("desc", "")
            author_info = item.get("author", {})
            statistics = item.get("statistics", {})
            interact_info = item.get("interact_info", {})

            play_count = statistics.get("play_count", 0) or interact_info.get("play_count", 0)
            digg_count = statistics.get("digg_count", 0) or interact_info.get("digg_count", 0)
            comment_count = statistics.get("comment_count", 0) or interact_info.get("comment_count", 0)
            share_count = statistics.get("share_count", 0) or interact_info.get("share_count", 0)
            collect_count = statistics.get("collect_count", 0) or interact_info.get("collect_count", 0)

            create_time = item.get("create_time", 0)
            created_at = datetime.fromtimestamp(create_time, tz=timezone.utc).isoformat() if create_time else None

            tags: list[str] = []
            for tag in item.get("text_extra", []):
                tag_name = tag.get("hashtag_name", "")
                if tag_name:
                    tags.append(tag_name)

            return {
                "video_id": str(video_id),
                "title": desc,
                "author": {
                    "uid": str(author_info.get("uid", "")),
                    "nickname": author_info.get("nickname", ""),
                    "avatar": author_info.get("avatar_larger", {}).get("url_list", [""])[0] if author_info.get("avatar_larger") else "",
                },
                "statistics": {
                    "play_count": int(play_count),
                    "digg_count": int(digg_count),
                    "comment_count": int(comment_count),
                    "share_count": int(share_count),
                    "collect_count": int(collect_count),
                },
                "tags": tags,
                "created_at": created_at,
                "share_url": item.get("share_url", ""),
            }
        except Exception as e:
            logger.error(f"Douyin parse video item error: {e}")
            return None

    def _parse_comment_item(self, item: dict[str, Any]) -> dict[str, Any] | None:
        try:
            if not item or not isinstance(item, dict):
                return None

            user = item.get("user", {})
            return {
                "comment_id": str(item.get("cid", "")),
                "content": item.get("text", ""),
                "digg_count": int(item.get("digg_count", 0)),
                "reply_count": int(item.get("reply_comment_total", 0)),
                "user": {
                    "uid": str(user.get("uid", "")),
                    "nickname": user.get("nickname", ""),
                },
                "created_at": item.get("create_time", 0),
            }
        except Exception as e:
            logger.error(f"Douyin parse comment item error: {e}")
            return None


douyin_scraper = DouyinScraper()
