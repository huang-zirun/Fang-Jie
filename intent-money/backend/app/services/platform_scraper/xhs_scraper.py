import logging
from typing import Any

import httpx

from app.config import settings
from app.services.platform_scraper.base_scraper import BasePlatformScraper

logger = logging.getLogger(__name__)

XHS_SEARCH_URL = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"
XHS_NOTE_DETAIL_URL = "https://edith.xiaohongshu.com/api/sns/web/v1/feed"
XHS_NOTE_COMMENTS_URL = "https://edith.xiaohongshu.com/api/sns/web/v2/comment/page"

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Origin": "https://www.xiaohongshu.com",
    "Referer": "https://www.xiaohongshu.com/",
    "Content-Type": "application/json;charset=UTF-8",
}


class XhsScraper(BasePlatformScraper):
    def __init__(self) -> None:
        self._cookie = settings.XHS_COOKIE

    def _build_headers(self) -> dict[str, str]:
        headers = {**_DEFAULT_HEADERS}
        if self._cookie:
            headers["Cookie"] = self._cookie
        return headers

    async def search_hot_notes(self, keyword: str, limit: int = 20) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                payload = {
                    "keyword": keyword,
                    "page": 1,
                    "page_size": min(limit, 20),
                    "search_id": "",
                    "sort": "general",
                    "note_type": 0,
                }
                resp = await client.post(
                    XHS_SEARCH_URL,
                    json=payload,
                    headers=self._build_headers(),
                )
                resp.raise_for_status()
                data = resp.json()

            items = data.get("data", {}).get("items", [])
            results: list[dict] = []
            for item in items[:limit]:
                note_card = item.get("note_card") or item.get("card") or {}
                interact = note_card.get("interact_info", {})
                user = note_card.get("user", {})

                results.append({
                    "note_id": note_card.get("note_id", ""),
                    "title": note_card.get("display_title", "") or note_card.get("title", ""),
                    "author": user.get("nickname", ""),
                    "author_id": user.get("user_id", ""),
                    "liked_count": interact.get("liked_count", "0"),
                    "collected_count": interact.get("collected_count", "0"),
                    "comment_count": interact.get("comment_count", "0"),
                    "share_count": interact.get("share_count", "0"),
                    "note_type": note_card.get("type", ""),
                    "tag_list": [t.get("name", "") for t in note_card.get("tag_list", [])],
                })

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"小红书搜索HTTP错误: {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            logger.error(f"小红书搜索请求异常: {e}")
            return []
        except Exception as e:
            logger.error(f"小红书搜索未知错误: {e}")
            return []

    async def get_note_detail(self, note_id: str) -> dict[str, Any] | None:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                payload = {
                    "source_note_id": note_id,
                    "image_scenes": ["CRD_WM_WEBP"],
                }
                resp = await client.post(
                    XHS_NOTE_DETAIL_URL,
                    json=payload,
                    headers=self._build_headers(),
                )
                resp.raise_for_status()
                data = resp.json()

            items = data.get("data", {}).get("items", [])
            if not items:
                return None

            note = items[0].get("note_card", {})
            interact = note.get("interact_info", {})
            user = note.get("user", {})

            return {
                "note_id": note.get("note_id", ""),
                "title": note.get("title", ""),
                "desc": note.get("desc", ""),
                "author": user.get("nickname", ""),
                "author_id": user.get("user_id", ""),
                "liked_count": interact.get("liked_count", "0"),
                "collected_count": interact.get("collected_count", "0"),
                "comment_count": interact.get("comment_count", "0"),
                "share_count": interact.get("share_count", "0"),
                "note_type": note.get("type", ""),
                "tag_list": [t.get("name", "") for t in note.get("tag_list", [])],
                "image_list": [img.get("url_default", "") for img in note.get("image_list", [])],
                "video": note.get("video", {}),
                "time": note.get("time", 0),
                "last_update_time": note.get("last_update_time", 0),
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"小红书笔记详情HTTP错误: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"小红书笔记详情请求异常: {e}")
            return None
        except Exception as e:
            logger.error(f"小红书笔记详情未知错误: {e}")
            return None

    async def get_note_comments(self, note_id: str, limit: int = 50) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                all_comments: list[dict] = []
                cursor = ""

                while len(all_comments) < limit:
                    params = {
                        "note_id": note_id,
                        "cursor": cursor,
                        "top_comment_id": "",
                        "image_scenes": "",
                    }
                    resp = await client.get(
                        XHS_NOTE_COMMENTS_URL,
                        params=params,
                        headers=self._build_headers(),
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    comments = data.get("data", {}).get("comments", [])
                    if not comments:
                        break

                    for c in comments:
                        user_info = c.get("user_info", {})
                        all_comments.append({
                            "comment_id": c.get("id", ""),
                            "content": c.get("content", ""),
                            "author": user_info.get("nickname", ""),
                            "author_id": user_info.get("user_id", ""),
                            "liked_count": c.get("like_count", "0"),
                            "sub_comment_count": c.get("sub_comment_count", "0"),
                            "create_time": c.get("create_time", 0),
                            "ip_location": c.get("ip_location", ""),
                            "sub_comments": [
                                {
                                    "comment_id": sc.get("id", ""),
                                    "content": sc.get("content", ""),
                                    "author": sc.get("user_info", {}).get("nickname", ""),
                                    "liked_count": sc.get("like_count", "0"),
                                }
                                for sc in c.get("sub_comments", [])
                            ],
                        })

                    has_more = data.get("data", {}).get("has_more", False)
                    cursor = data.get("data", {}).get("cursor", "")
                    if not has_more:
                        break

                return all_comments[:limit]

        except httpx.HTTPStatusError as e:
            logger.error(f"小红书评论HTTP错误: {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            logger.error(f"小红书评论请求异常: {e}")
            return []
        except Exception as e:
            logger.error(f"小红书评论未知错误: {e}")
            return []

    async def search_hot_videos(self, keyword: str, limit: int = 20) -> list[dict[str, Any]]:
        logger.warning("小红书爬虫不支持视频搜索")
        return []

    async def get_video_detail(self, video_id: str) -> dict[str, Any] | None:
        logger.warning("小红书爬虫不支持视频详情")
        return None

    async def get_video_comments(self, video_id: str, limit: int = 50) -> list[dict[str, Any]]:
        logger.warning("小红书爬虫不支持视频评论")
        return []

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://www.xiaohongshu.com",
                    headers=_DEFAULT_HEADERS,
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"小红书健康检查失败: {e}")
            return False
