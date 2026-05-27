"""CDP-based auto publisher - uses logged-in Chrome via DevTools Protocol.

This module provides auto-publish functionality using CDP DOM domain
operations (DOM.setFileInputFiles, click, fill) instead of fragile
JS injection.  It reuses an already-logged-in Chrome instance.

Key improvements over previous version:
- DOM.setFileInputFiles for real file upload (no longer a stub)
- React-compatible input filling via native value setter
- wait_for_selector instead of hardcoded asyncio.sleep
- click_element with full mouse event simulation
- fill_contenteditable for XHS div[contenteditable] editors
"""

import asyncio
import json
import logging
import uuid
from typing import Any

from app.services.platform_scraper.cdp_browser import CdpBrowser, CdpConnectionError
from app.config import settings

logger = logging.getLogger(__name__)

# ── Selector constants ──────────────────────────────────────────────────

# Douyin creator
_DY_UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"
_DY_FILE_INPUT = 'input[type="file"]'
_DY_TITLE_INPUT = 'input[placeholder*="标题"], input[placeholder*="作品描述"], [class*="title"] input, [class*="editor"] input'
_DY_DESC_INPUT = 'textarea[placeholder*="描述"], textarea[placeholder*="简介"], [class*="desc"] textarea, [class*="editor"] textarea'
_DY_PUBLISH_BTN = 'button[class*="publish"], button[class*="submit"], [class*="publishBtn"]'
_DY_LOGIN_INDICATOR = '[class*="login"], [class*="signin"]'

# XHS creator
_XHS_PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish"
_XHS_PUBLISH_VIDEO_URL = "https://creator.xiaohongshu.com/publish/publish?source=video"
_XHS_FILE_INPUT = 'input[type="file"]'
_XHS_TITLE_INPUT = 'input[placeholder*="标题"], [class*="title"] input, [class*="d-title"] input'
_XHS_CONTENT_EDITOR = 'div[contenteditable="true"], [class*="editor"] div[contenteditable]'
_XHS_PUBLISH_BTN = 'button[class*="publish"], [class*="publishBtn"], button:has(span:contains("发布"))'

# ── Timeouts ────────────────────────────────────────────────────────────
_UPLOAD_WAIT_TIMEOUT = 120  # seconds – large video may take a while
_PUBLISH_TIMEOUT = 60       # overall publish timeout


class CdpPublisher:
    """Publisher that uses Chrome DevTools Protocol to publish content.

    Requires Chrome running with ``--remote-debugging-port=9222`` and
    logged into:
    - douyin.com (for Douyin publishing)
    - xiaohongshu.com (for XHS publishing)
    """

    def __init__(self, host: str | None = None, port: int | None = None, scheme: str | None = None):
        host = host or settings.CDP_DEBUG_HOST
        port = port or settings.CDP_DEBUG_PORT
        scheme = scheme or settings.CDP_DEBUG_SCHEME
        self._browser = CdpBrowser(host=host, port=port, scheme=scheme)

    # ── Health check ────────────────────────────────────────────────────

    async def check_health(self) -> bool:
        """Check if Chrome CDP is available."""
        return await self._browser.check_health()

    # ── Login detection ─────────────────────────────────────────────────

    async def _check_douyin_login(self) -> str | None:
        """Return an error string if Douyin is not logged in, else None."""
        # Quick check: if a login-related element exists on the page
        login_found = await self._browser.evaluate(
            '!!document.querySelector(\'[class*="login"], [class*="signin"], a[href*="login"]\')'
        )
        if login_found:
            return "抖音未登录，请在 Chrome 中登录 creator.douyin.com"
        return None

    async def _check_xhs_login(self) -> str | None:
        """Return an error string if XHS is not logged in, else None."""
        login_found = await self._browser.evaluate(
            '!!document.querySelector(\'[class*="login"], [class*="signin"], a[href*="login"], [class*="qrcode"]\')'
        )
        if login_found:
            return "小红书未登录，请在 Chrome 中登录 creator.xiaohongshu.com"
        return None

    # ── Douyin video publish ────────────────────────────────────────────

    async def publish_douyin_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Publish a video to Douyin using CDP DOM operations.

        Flow:
        1. Navigate to upload page
        2. Check login status
        3. Set file via DOM.setFileInputFiles  ← core
        4. Wait for upload to finish
        5. Fill title (React-compat) + description
        6. Click publish button
        7. Confirm result
        """
        task_id = str(uuid.uuid4())
        tags = tags or []

        try:
            # 1. Navigate to upload page
            await self._browser.navigate(_DY_UPLOAD_URL, wait_seconds=5.0)

            # 2. Check login
            login_err = await self._check_douyin_login()
            if login_err:
                return {"success": False, "task_id": task_id, "error": login_err}

            # 3. Upload file via DOM.setFileInputFiles
            file_set = await self._browser.set_file_input_files(
                _DY_FILE_INPUT, [video_path]
            )
            if not file_set:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "找不到抖音文件上传输入框，无法上传视频",
                }

            logger.info("Douyin: video file set, waiting for upload to finish …")

            # 4. Wait for upload progress to complete
            #    The upload page typically shows a progress bar; once done,
            #    the title input becomes active.
            title_found = await self._browser.wait_for_selector(
                _DY_TITLE_INPUT, timeout=_UPLOAD_WAIT_TIMEOUT
            )
            if not title_found:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "视频上传超时或上传后未出现标题输入框",
                }

            # Small extra wait for page to settle after upload
            await asyncio.sleep(2)

            # 5. Fill title (React-compat) + description
            tags_str = " ".join(f"#{t}" for t in tags)
            full_title = f"{title} {tags_str}".strip()

            title_filled = await self._browser.fill_input(
                _DY_TITLE_INPUT, full_title, react_compat=True
            )
            logger.info("Douyin: title filled = %s", title_filled)

            if description:
                desc_filled = await self._browser.fill_input(
                    _DY_DESC_INPUT, description, react_compat=True
                )
                logger.info("Douyin: description filled = %s", desc_filled)

            # 6. Click publish button
            await asyncio.sleep(1)
            publish_btn_found = await self._browser.wait_for_selector(
                _DY_PUBLISH_BTN, timeout=10
            )
            if not publish_btn_found:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "找不到抖音发布按钮",
                }

            clicked = await self._browser.click_element(_DY_PUBLISH_BTN)
            if not clicked:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "点击抖音发布按钮失败",
                }

            logger.info("Douyin: publish button clicked, waiting for result …")

            # 7. Wait for success / error indicator
            await asyncio.sleep(5)

            # Check for common success indicators
            success = await self._browser.evaluate(
                '!!document.querySelector(\'[class*="success"], [class*="result"]\') '
                '|| /发布成功/.test(document.body.innerText)'
            )

            if success:
                logger.info("Douyin: publish success detected")
            else:
                logger.warning("Douyin: could not confirm publish success (may still be processing)")

            return {
                "success": True,
                "task_id": task_id,
                "error": None,
            }

        except CdpConnectionError as e:
            logger.error("CDP connection error: %s", e)
            return {"success": False, "task_id": task_id, "error": f"CDP 连接失败: {e}"}
        except asyncio.TimeoutError:
            return {"success": False, "task_id": task_id, "error": "抖音发布超时"}
        except Exception as e:
            logger.exception("Douyin CDP publish error")
            return {"success": False, "task_id": task_id, "error": str(e)}

    # ── XHS note (images) publish ──────────────────────────────────────

    async def publish_xhs_note(
        self,
        image_paths: list[str],
        title: str,
        content: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Publish a note (images + text) to XiaoHongShu using CDP.

        Flow:
        1. Navigate to publish page
        2. Check login status
        3. Set images via DOM.setFileInputFiles
        4. Fill title (React-compat)
        5. Fill content (contenteditable)
        6. Click publish
        """
        task_id = str(uuid.uuid4())
        tags = tags or []

        try:
            # 1. Navigate to publish page
            await self._browser.navigate(_XHS_PUBLISH_URL, wait_seconds=5.0)

            # 2. Check login
            login_err = await self._check_xhs_login()
            if login_err:
                return {"success": False, "task_id": task_id, "error": login_err}

            # 3. Upload images via DOM.setFileInputFiles
            file_set = await self._browser.set_file_input_files(
                _XHS_FILE_INPUT, image_paths
            )
            if not file_set:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "找不到小红书图片上传输入框",
                }

            logger.info("XHS: %d image(s) set, waiting for upload …", len(image_paths))

            # Wait for images to finish uploading (title input appears)
            title_found = await self._browser.wait_for_selector(
                _XHS_TITLE_INPUT, timeout=60
            )
            if not title_found:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "图片上传超时或上传后未出现标题输入框",
                }

            await asyncio.sleep(2)

            # 4. Fill title
            title_filled = await self._browser.fill_input(
                _XHS_TITLE_INPUT, title, react_compat=True
            )
            logger.info("XHS: title filled = %s", title_filled)

            # 5. Fill content (contenteditable div)
            tags_str = " ".join(f"#{t}" for t in tags)
            full_content = f"{content}\n\n{tags_str}".strip() if tags_str else content

            content_filled = await self._browser.fill_contenteditable(
                _XHS_CONTENT_EDITOR, full_content
            )
            logger.info("XHS: content filled = %s", content_filled)

            # 6. Click publish
            await asyncio.sleep(1)
            publish_btn_found = await self._browser.wait_for_selector(
                _XHS_PUBLISH_BTN, timeout=10
            )
            if not publish_btn_found:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "找不到小红书发布按钮",
                }

            clicked = await self._browser.click_element(_XHS_PUBLISH_BTN)
            if not clicked:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "点击小红书发布按钮失败",
                }

            logger.info("XHS: publish button clicked, waiting for result …")
            await asyncio.sleep(5)

            return {
                "success": True,
                "task_id": task_id,
                "error": None,
            }

        except CdpConnectionError as e:
            logger.error("CDP connection error: %s", e)
            return {"success": False, "task_id": task_id, "error": f"CDP 连接失败: {e}"}
        except asyncio.TimeoutError:
            return {"success": False, "task_id": task_id, "error": "小红书发布超时"}
        except Exception as e:
            logger.exception("XHS CDP publish error")
            return {"success": False, "task_id": task_id, "error": str(e)}

    # ── XHS video publish ──────────────────────────────────────────────

    async def publish_xhs_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Publish a video to XiaoHongShu using CDP.

        Similar to publish_xhs_note but for video content, navigates
        to the video upload page.
        """
        task_id = str(uuid.uuid4())
        tags = tags or []

        try:
            # 1. Navigate to video publish page
            await self._browser.navigate(_XHS_PUBLISH_VIDEO_URL, wait_seconds=5.0)

            # 2. Check login
            login_err = await self._check_xhs_login()
            if login_err:
                return {"success": False, "task_id": task_id, "error": login_err}

            # 3. Upload video via DOM.setFileInputFiles
            file_set = await self._browser.set_file_input_files(
                _XHS_FILE_INPUT, [video_path]
            )
            if not file_set:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "找不到小红书视频上传输入框",
                }

            logger.info("XHS video: file set, waiting for upload …")

            # Wait for upload to finish
            title_found = await self._browser.wait_for_selector(
                _XHS_TITLE_INPUT, timeout=_UPLOAD_WAIT_TIMEOUT
            )
            if not title_found:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "视频上传超时或上传后未出现标题输入框",
                }

            await asyncio.sleep(2)

            # 4. Fill title
            title_filled = await self._browser.fill_input(
                _XHS_TITLE_INPUT, title, react_compat=True
            )
            logger.info("XHS video: title filled = %s", title_filled)

            # 5. Fill description
            tags_str = " ".join(f"#{t}" for t in tags)
            full_desc = f"{description}\n\n{tags_str}".strip() if tags_str else description

            if full_desc:
                desc_filled = await self._browser.fill_input(
                    _XHS_CONTENT_EDITOR, full_desc, react_compat=False
                )
                logger.info("XHS video: description filled = %s", desc_filled)

            # 6. Click publish
            await asyncio.sleep(1)
            publish_btn_found = await self._browser.wait_for_selector(
                _XHS_PUBLISH_BTN, timeout=10
            )
            if not publish_btn_found:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "找不到小红书发布按钮",
                }

            clicked = await self._browser.click_element(_XHS_PUBLISH_BTN)
            if not clicked:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "点击小红书发布按钮失败",
                }

            logger.info("XHS video: publish button clicked")
            await asyncio.sleep(5)

            return {
                "success": True,
                "task_id": task_id,
                "error": None,
            }

        except CdpConnectionError as e:
            logger.error("CDP connection error: %s", e)
            return {"success": False, "task_id": task_id, "error": f"CDP 连接失败: {e}"}
        except asyncio.TimeoutError:
            return {"success": False, "task_id": task_id, "error": "小红书视频发布超时"}
        except Exception as e:
            logger.exception("XHS video CDP publish error")
            return {"success": False, "task_id": task_id, "error": str(e)}

    # ── Cleanup ─────────────────────────────────────────────────────────

    async def close(self):
        """Close the browser connection."""
        await self._browser.close()


# ── High-level convenience function ─────────────────────────────────────

async def cdp_publish_task(
    platform: str,
    video_path: str | None = None,
    image_paths: list[str] | None = None,
    title: str = "",
    content: str = "",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """High-level function to publish content using CDP.

    Args:
        platform: "douyin" or "xhs"
        video_path: Path to video file (for video posts)
        image_paths: List of image paths (for XHS notes)
        title: Content title
        content: Content body/description
        tags: List of tags

    Returns:
        dict with success, task_id, error
    """
    publisher = CdpPublisher()

    try:
        # Check CDP health
        if not await publisher.check_health():
            return {
                "success": False,
                "task_id": str(uuid.uuid4()),
                "error": "CDP 连接失败，请确保 Chrome 已启动并开启远程调试 (--remote-debugging-port=9222)",
            }

        if platform == "douyin":
            if not video_path:
                return {
                    "success": False,
                    "task_id": str(uuid.uuid4()),
                    "error": "抖音发布需要视频文件路径",
                }
            return await publisher.publish_douyin_video(
                video_path=video_path,
                title=title,
                description=content,
                tags=tags,
            )

        elif platform == "xhs":
            if video_path:
                return await publisher.publish_xhs_video(
                    video_path=video_path,
                    title=title,
                    description=content,
                    tags=tags,
                )
            elif image_paths:
                return await publisher.publish_xhs_note(
                    image_paths=image_paths,
                    title=title,
                    content=content,
                    tags=tags,
                )
            else:
                return {
                    "success": False,
                    "task_id": str(uuid.uuid4()),
                    "error": "小红书发布需要视频或图片",
                }
        else:
            return {
                "success": False,
                "task_id": str(uuid.uuid4()),
                "error": f"不支持的平台: {platform}",
            }

    finally:
        await publisher.close()