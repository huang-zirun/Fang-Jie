import json
import logging
from typing import Any

from app.services.platform_scraper.base_scraper import BasePlatformScraper
from app.services.platform_scraper.cdp_browser import CdpBrowser, CdpConnectionError
from app.config import settings

logger = logging.getLogger(__name__)

XHS_SEARCH_URL = "https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes&type=51&sort={sort}"
XHS_NOTE_DETAIL_URL = "https://www.xiaohongshu.com/explore/{note_id}"
XHS_BASE_URL = "https://www.xiaohongshu.com"


class CdpXhsScraper(BasePlatformScraper):
    """Xiaohongshu scraper via Chrome DevTools Protocol.

    Requires Chrome running with --remote-debugging-port=9222 and logged into xiaohongshu.com.
    """

    def __init__(self, browser: CdpBrowser | None = None):
        self._browser = browser or CdpBrowser(
            host=settings.CDP_DEBUG_HOST,
            port=settings.CDP_DEBUG_PORT,
            scheme=settings.CDP_DEBUG_SCHEME,
        )

    async def search_hot_notes(self, keyword: str, limit: int = 20, sort: str = "likes") -> list[dict[str, Any]]:
        """搜索小红书笔记

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            sort: 排序方式，general=综合, time=最新, likes=最多点赞(默认), comments=最多评论, favorites=最多收藏
        """
        url = XHS_SEARCH_URL.format(keyword=keyword, sort=sort)
        try:
            await self._browser.navigate(url, wait_seconds=6.0)
            raw = await self._browser.evaluate("""
            (function() {
                var cards = document.querySelectorAll('.note-item');
                var results = [];
                cards.forEach(function(card, i) {
                    if (i >= """ + str(limit) + """) return;
                    // Support both .footer and .card-bottom-wrapper structures
                    var container = card.querySelector('.footer') || card.querySelector('.card-bottom-wrapper');
                    var titleEl = container ? container.querySelector('.title') : null;
                    var authorEl = container ? container.querySelector('.author .name') : card.querySelector('.author .name');
                    var likeEl = container ? container.querySelector('.like-wrapper .count') : card.querySelector('.like-wrapper .count');
                    var linkEl = container ? (container.querySelector('a.title') || container.querySelector('a[href*="explore"]')) : card.querySelector('a[href*="explore"]');
                    var imgEl = card.querySelector('img[src]');
                    // Extract note_id from link
                    var noteId = '';
                    if (linkEl) {
                        var m = linkEl.href.match(/explore\\/([a-f0-9]+)/);
                        if (m) noteId = m[1];
                    }
                    results.push({
                        note_id: noteId,
                        title: titleEl ? titleEl.textContent.trim() : '',
                        author: authorEl ? authorEl.textContent.trim() : '',
                        author_id: '',
                        liked_count: likeEl ? likeEl.textContent.trim() : '0',
                        collected_count: '0',
                        comment_count: '0',
                        share_count: '0',
                        note_type: '',
                        tag_list: [],
                        image: imgEl ? imgEl.src : '',
                        link: linkEl ? linkEl.href : ''
                    });
                });
                return JSON.stringify(results);
            })()
            """)
            if not raw:
                logger.warning(f"XHS CDP search returned empty for keyword '{keyword}'")
                return []
            return list(json.loads(raw))
        except CdpConnectionError as e:
            logger.error(f"XHS CDP connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"XHS CDP search error: {e}")
            return []

    async def get_note_detail(self, note_id: str) -> dict[str, Any] | None:
        url = XHS_NOTE_DETAIL_URL.format(note_id=note_id)
        try:
            await self._browser.navigate(url, wait_seconds=5.0)
            raw = await self._browser.evaluate("""
            (function() {
                var titleEl = document.querySelector('.title, #detail-title');
                var descEl = document.querySelector('.desc, #detail-desc');
                var authorEl = document.querySelector('.author .user-name, .username');
                var likeEl = document.querySelector('.like-wrapper .count, [class*="like"] span');
                var collectEl = document.querySelector('.collect-wrapper .count, [class*="collect"] span');
                var commentEl = document.querySelector('.comment-wrapper .count, [class*="comment"] span');
                var imgEls = document.querySelectorAll('.swiper-slide img, .note-slider img, [class*="image"] img');
                var imgList = [];
                imgEls.forEach(function(img) { if (img.src) imgList.push(img.src); });
                return JSON.stringify({
                    note_id: '""" + note_id + """',
                    title: titleEl ? titleEl.textContent.trim() : '',
                    desc: descEl ? descEl.textContent.trim() : '',
                    author: authorEl ? authorEl.textContent.trim() : '',
                    author_id: '',
                    liked_count: likeEl ? likeEl.textContent.trim() : '0',
                    collected_count: collectEl ? collectEl.textContent.trim() : '0',
                    comment_count: commentEl ? commentEl.textContent.trim() : '0',
                    share_count: '0',
                    note_type: '',
                    tag_list: [],
                    image_list: imgList,
                    video: {},
                    time: 0,
                    last_update_time: 0
                });
            })()
            """)
            if not raw:
                return None
            return dict(json.loads(raw))
        except CdpConnectionError as e:
            logger.error(f"XHS CDP note detail connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"XHS CDP note detail error: {e}")
            return None

    async def get_note_comments(self, note_id: str, limit: int = 50) -> list[dict[str, Any]]:
        url = XHS_NOTE_DETAIL_URL.format(note_id=note_id)
        try:
            await self._browser.navigate(url, wait_seconds=5.0)
            # Scroll down to load comments
            await self._browser.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            import asyncio
            await asyncio.sleep(3)

            raw = await self._browser.evaluate("""
            (function() {
                var comments = document.querySelectorAll('[class*="comment-item"], .comment-item, [data-testid*="comment"]');
                var results = [];
                comments.forEach(function(c, i) {
                    if (i >= """ + str(limit) + """) return;
                    var authorEl = c.querySelector('[class*="author"] [class*="name"], .user-name, [class*="nickname"]');
                    var contentEl = c.querySelector('[class*="content"], .comment-text, [class*="text"]');
                    var likeEl = c.querySelector('[class*="like"] span, [class*="count"]');
                    var timeEl = c.querySelector('[class*="time"], .date');
                    if (!contentEl) return;
                    results.push({
                        comment_id: c.getAttribute('data-id') || '',
                        content: contentEl ? contentEl.textContent.trim() : '',
                        author: authorEl ? authorEl.textContent.trim() : '',
                        author_id: '',
                        liked_count: likeEl ? likeEl.textContent.trim() : '0',
                        sub_comment_count: '0',
                        create_time: timeEl ? timeEl.textContent.trim() : '',
                        ip_location: '',
                        sub_comments: []
                    });
                });
                return JSON.stringify(results);
            })()
            """)
            if not raw:
                return []
            return list(json.loads(raw))
        except CdpConnectionError as e:
            logger.error(f"XHS CDP comments connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"XHS CDP comments error: {e}")
            return []

    async def search_hot_videos(self, keyword: str, limit: int = 20) -> list[dict[str, Any]]:
        logger.warning("CdpXhsScraper does not support video search")
        return []

    async def get_video_detail(self, video_id: str) -> dict[str, Any] | None:
        logger.warning("CdpXhsScraper does not support video detail")
        return None

    async def get_video_comments(self, video_id: str, limit: int = 50) -> list[dict[str, Any]]:
        logger.warning("CdpXhsScraper does not support video comments")
        return []

    async def check_health(self) -> bool:
        return await self._browser.check_health()


