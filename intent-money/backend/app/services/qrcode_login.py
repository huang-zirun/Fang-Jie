import asyncio
import base64
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _get_stealth_js_path() -> Path:
    return Path(__file__).parent.parent / "utils" / "stealth.min.js"


class QrLoginSession:
    def __init__(self, session_id: str, platform: str, user_id: str):
        self.session_id = session_id
        self.platform = platform
        self.user_id = user_id
        self.status = "pending"
        self.qr_code_url: str | None = None
        self.qr_code_base64: str | None = None
        self.browser_context: Any = None
        self.page: Any = None
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = self.created_at + timedelta(minutes=5)
        self._playwright: Any = None
        self._browser: Any = None
        self._storage_state: dict | None = None


_sessions: dict[str, QrLoginSession] = {}

PLATFORM_LOGIN_URLS = {
    "xhs": "https://creator.xiaohongshu.com/login",
    "douyin": "https://www.douyin.com",
}

PLATFORM_LOGIN_URL_PREFIXES = {
    "xhs": "https://creator.xiaohongshu.com/login",
    "douyin": "https://www.douyin.com/login",
}

PLATFORM_QR_SELECTORS = {
    "xhs": "div[class*='login-box'] img, [class*='qrcode'] img, img.css-wemwzq",
    "douyin": "[class*='qrcode'] img, [class*='login'] img, canvas",
}


def _is_login_completed(platform: str, current_url: str) -> bool:
    login_prefix = PLATFORM_LOGIN_URL_PREFIXES.get(platform)
    if not login_prefix:
        return False
    return not current_url.startswith(login_prefix)


async def start_qr_login(platform: str, user_id: str) -> dict:
    if platform not in PLATFORM_LOGIN_URLS:
        return {"success": False, "error": f"不支持的平台: {platform}"}

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"success": False, "error": "Playwright 未安装，请运行: pip install playwright && playwright install chromium"}

    session_id = str(uuid.uuid4())
    session = QrLoginSession(session_id, platform, user_id)
    _sessions[session_id] = session

    try:
        pw = await async_playwright().start()
        session._playwright = pw
        browser = await pw.chromium.launch(
            headless=True,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        session._browser = browser
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )

        stealth_js_path = _get_stealth_js_path()
        if stealth_js_path.exists():
            await context.add_init_script(path=str(stealth_js_path))
            logger.debug(f"已注入隐身脚本: {stealth_js_path}")

        session.browser_context = context
        page = await context.new_page()
        session.page = page

        login_url = PLATFORM_LOGIN_URLS[platform]
        await page.goto(login_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)

        selector = PLATFORM_QR_SELECTORS.get(platform, "img")
        try:
            qr_element = await page.wait_for_selector(selector, timeout=10000)
            if qr_element:
                screenshot_bytes = await qr_element.screenshot(type="png")
                qr_base64 = base64.b64encode(screenshot_bytes).decode("ascii")
                session.qr_code_base64 = f"data:image/png;base64,{qr_base64}"
                session.qr_code_url = f"data:image/png;base64,{qr_base64}"
        except Exception as e:
            logger.warning(f"未找到{platform}二维码元素: {e}")
            screenshot_bytes = await page.screenshot(type="png")
            qr_base64 = base64.b64encode(screenshot_bytes).decode("ascii")
            session.qr_code_base64 = f"data:image/png;base64,{qr_base64}"
            session.qr_code_url = f"data:image/png;base64,{qr_base64}"

        asyncio.create_task(_poll_login_status(session))

        return {
            "success": True,
            "login_session_id": session_id,
            "qr_code_url": session.qr_code_url,
            "expires_at": session.expires_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"二维码登录启动失败: {e}")
        session.status = "failed"
        await _cleanup_session(session_id)
        error_msg = str(e)
        if "Executable doesn't exist" in error_msg or "Executable doesn\'t exist" in error_msg:
            return {
                "success": False,
                "error": "Playwright 浏览器未安装，请在 backend 目录下运行: uv run playwright install chromium",
            }
        return {"success": False, "error": f"启动登录失败: {error_msg}"}


async def _poll_login_status(session: QrLoginSession) -> None:
    deadline = session.expires_at
    while datetime.now(timezone.utc) < deadline:
        try:
            if session.page:
                current_url = session.page.url
                if _is_login_completed(session.platform, current_url):
                    await asyncio.sleep(2)
                    storage_state = await session.browser_context.storage_state()
                    session._storage_state = storage_state
                    session.status = "confirmed"
                    logger.info(
                        f"二维码登录结果: {session.platform}已确认, "
                        f"跳转至{current_url}, "
                        f"获取{len(storage_state.get('cookies', []))}个cookie"
                    )
                    await _cleanup_session(session.session_id)
                    return
        except Exception:
            pass
        await asyncio.sleep(2)
    session.status = "expired"
    await _cleanup_session(session.session_id)


async def check_login_status(session_id: str) -> dict:
    session = _sessions.get(session_id)
    if not session:
        return {"status": "expired", "message": "登录会话不存在或已过期"}
    return {
        "status": session.status,
        "message": _status_message(session.status),
        "storage_state": getattr(session, "_storage_state", None),
    }


def _status_message(status: str) -> str:
    messages = {
        "pending": "等待扫码",
        "scanned": "已扫码，等待确认",
        "confirmed": "登录成功",
        "expired": "二维码已过期",
        "failed": "登录失败",
    }
    return messages.get(status, "未知状态")


async def _cleanup_session(session_id: str) -> None:
    session = _sessions.get(session_id)
    if not session:
        return
    try:
        if session.page:
            await session.page.close()
    except Exception:
        pass
    try:
        if session.browser_context:
            await session.browser_context.close()
    except Exception:
        pass
    try:
        if session._browser:
            await session._browser.close()
    except Exception:
        pass
    try:
        if session._playwright:
            await session._playwright.stop()
    except Exception:
        pass


async def cleanup_expired() -> None:
    now = datetime.now(timezone.utc)
    expired_ids = [
        sid for sid, s in _sessions.items()
        if s.expires_at < now and s.status in ("pending", "scanned")
    ]
    for sid in expired_ids:
        _sessions[sid].status = "expired"
        await _cleanup_session(sid)
