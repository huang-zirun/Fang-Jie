import json
import logging
import re
import uuid
from typing import Any

from app.services.platform_scraper.base_scraper import BasePlatformScraper
from app.services.platform_scraper.cdp_browser import CdpBrowser, CdpConnectionError

logger = logging.getLogger(__name__)

DOUYIN_SEARCH_URL = "https://www.douyin.com/search/{keyword}?type=video&sort_type={sort_type}"
DOUYIN_VIDEO_URL = "https://www.douyin.com/video/{video_id}"
DOUYIN_BASE_URL = "https://www.douyin.com"

# Pattern: duration + likes + title + @author + time_ago
_VIDEO_PATTERN = re.compile(
    r"(\d+:\d+)\n([\d.]+万?)\n(.+?)\n@(.+?)\n(.+?)(?=\n\d+:\d+|$)",
    re.DOTALL,
)


class CdpDouyinScraper(BasePlatformScraper):
    """Douyin scraper via Chrome DevTools Protocol.

    Requires Chrome running with --remote-debugging-port=9222 and logged into douyin.com.
    """

    def __init__(self, browser: CdpBrowser | None = None):
        self._browser = browser or CdpBrowser()

    async def search_hot_videos(self, keyword: str, limit: int = 20, sort_type: int = 1) -> list[dict[str, Any]]:
        """搜索抖音视频

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            sort_type: 排序方式，0=综合排序, 1=最多点赞(默认), 2=最新发布
        """
        url = DOUYIN_SEARCH_URL.format(keyword=keyword, sort_type=sort_type)
        try:
            await self._browser.navigate(url, wait_seconds=7.0)
            text = await self._browser.get_page_text()
            if not text:
                logger.warning(f"Douyin CDP search returned empty for keyword '{keyword}'")
                return []

            matches = _VIDEO_PATTERN.findall(text)
            results: list[dict[str, Any]] = []
            for duration, likes, title, author, time_ago in matches[:limit]:
                title = title.strip()
                author = author.strip()
                likes_num = self._parse_count(likes)

                results.append({
                    "video_id": str(uuid.uuid4()),  # CDP doesn't expose video IDs directly
                    "title": title,
                    "author": {
                        "uid": "",
                        "nickname": author,
                        "avatar": "",
                    },
                    "statistics": {
                        "play_count": 0,
                        "digg_count": likes_num,
                        "comment_count": 0,
                        "share_count": 0,
                        "collect_count": 0,
                    },
                    "tags": self._extract_tags(title),
                    "created_at": time_ago.strip(),
                    "share_url": "",
                    "duration": duration,
                })

            logger.info(f"Douyin CDP search found {len(results)} videos for keyword '{keyword}'")
            return results
        except CdpConnectionError as e:
            logger.error(f"Douyin CDP connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"Douyin CDP search error: {e}")
            return []

    async def get_video_detail(self, video_id: str) -> dict[str, Any] | None:
        url = DOUYIN_VIDEO_URL.format(video_id=video_id)
        try:
            await self._browser.navigate(url, wait_seconds=5.0)
            raw = await self._browser.evaluate("""
            (function() {
                var titleEl = document.querySelector('[class*="title"], .title');
                var authorEl = document.querySelector('[class*="author"] [class*="name"], .author-name');
                var descEl = document.querySelector('[class*="desc"], .desc');
                var likeEl = document.querySelector('[class*="like"] span, [class*="digg"] span');
                var commentEl = document.querySelector('[class*="comment"] span');
                var shareEl = document.querySelector('[class*="share"] span');
                return JSON.stringify({
                    video_id: '""" + video_id + """',
                    title: titleEl ? titleEl.textContent.trim() : '',
                    desc: descEl ? descEl.textContent.trim() : '',
                    author: authorEl ? authorEl.textContent.trim() : '',
                    liked_count: likeEl ? likeEl.textContent.trim() : '0',
                    comment_count: commentEl ? commentEl.textContent.trim() : '0',
                    share_count: shareEl ? shareEl.textContent.trim() : '0',
                });
            })()
            """)
            if not raw:
                return None
            data = json.loads(raw)
            return {
                "video_id": data.get("video_id", video_id),
                "title": data.get("title", ""),
                "author": {"uid": "", "nickname": data.get("author", ""), "avatar": ""},
                "statistics": {
                    "play_count": 0,
                    "digg_count": self._parse_count(data.get("liked_count", "0")),
                    "comment_count": self._parse_count(data.get("comment_count", "0")),
                    "share_count": self._parse_count(data.get("share_count", "0")),
                    "collect_count": 0,
                },
                "tags": self._extract_tags(data.get("title", "")),
                "created_at": None,
                "share_url": url,
            }
        except CdpConnectionError as e:
            logger.error(f"Douyin CDP video detail connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Douyin CDP video detail error: {e}")
            return None

    async def get_video_comments(self, video_id: str, limit: int = 50) -> list[dict[str, Any]]:
        url = DOUYIN_VIDEO_URL.format(video_id=video_id)
        try:
            await self._browser.navigate(url, wait_seconds=5.0)
            await self._browser.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            import asyncio
            await asyncio.sleep(3)

            raw = await self._browser.evaluate("""
            (function() {
                var comments = document.querySelectorAll('[class*="comment-item"], .comment-item');
                var results = [];
                comments.forEach(function(c, i) {
                    if (i >= """ + str(limit) + """) return;
                    var authorEl = c.querySelector('[class*="author"] [class*="name"], .user-name');
                    var contentEl = c.querySelector('[class*="content"], .comment-text');
                    var likeEl = c.querySelector('[class*="like"] span, [class*="count"]');
                    var timeEl = c.querySelector('[class*="time"], .date');
                    if (!contentEl) return;
                    results.push({
                        comment_id: c.getAttribute('data-id') || '',
                        content: contentEl ? contentEl.textContent.trim() : '',
                        digg_count: likeEl ? parseInt(likeEl.textContent.trim()) || 0 : 0,
                        reply_count: 0,
                        user: {
                            uid: '',
                            nickname: authorEl ? authorEl.textContent.trim() : ''
                        },
                        created_at: timeEl ? timeEl.textContent.trim() : ''
                    });
                });
                return JSON.stringify(results);
            })()
            """)
            if not raw:
                return []
            return list(json.loads(raw))
        except CdpConnectionError as e:
            logger.error(f"Douyin CDP comments connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"Douyin CDP comments error: {e}")
            return []

    async def search_hot_notes(self, keyword: str, limit: int = 20) -> list[dict[str, Any]]:
        logger.warning("CdpDouyinScraper does not support note search")
        return []

    async def get_note_detail(self, note_id: str) -> dict[str, Any] | None:
        logger.warning("CdpDouyinScraper does not support note detail")
        return None

    async def get_note_comments(self, note_id: str, limit: int = 50) -> list[dict[str, Any]]:
        logger.warning("CdpDouyinScraper does not support note comments")
        return []

    async def check_health(self) -> bool:
        return await self._browser.check_health()

    @staticmethod
    def _parse_count(value: str) -> int:
        """Parse count string like '1.5万' to int."""
        if not value:
            return 0
        value = str(value).strip()
        if "万" in value:
            return int(float(value.replace("万", "")) * 10000)
        try:
            return int(value)
        except ValueError:
            return 0

    @staticmethod
    def _extract_tags(text: str) -> list[str]:
        """Extract hashtags from text."""
        return [tag for tag in re.findall(r"#([^#\s]+)", text)]
