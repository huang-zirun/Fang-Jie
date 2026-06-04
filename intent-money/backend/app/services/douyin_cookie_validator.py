import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DOUYIN_CREATOR_URL = "https://creator.douyin.com/creator-micro/content/upload"
DOUYIN_LOGIN_MARKERS = ["扫码登录", "手机号登录"]


def _get_stealth_js_path() -> Path:
    return Path(__file__).parent.parent / "utils" / "stealth.min.js"


def _parse_cookie_string(cookie_str: str) -> list[dict]:
    cookies = []
    for item in cookie_str.split(";"):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            continue
        name, _, value = item.partition("=")
        cookies.append({
            "name": name.strip(),
            "value": value.strip(),
            "domain": ".douyin.com",
            "path": "/",
        })
    return cookies


def _detect_cookie_format(cookie_data: str) -> str:
    try:
        parsed = json.loads(cookie_data)
        if isinstance(parsed, dict) and "cookies" in parsed:
            return "storage_state"
    except (json.JSONDecodeError, TypeError):
        pass
    return "cookie_string"


async def validate_douyin_cookie(cookie_data: str) -> bool:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright 未安装")
        return False

    stealth_js_path = _get_stealth_js_path()
    cookie_format = _detect_cookie_format(cookie_data)

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"],
            )
            try:
                if cookie_format == "storage_state":
                    storage_state = json.loads(cookie_data)
                    context = await browser.new_context(storage_state=storage_state)
                else:
                    cookies = _parse_cookie_string(cookie_data)
                    if not cookies:
                        logger.warning("Cookie 字符串解析失败，没有有效的 Cookie")
                        return False
                    context = await browser.new_context()
                    await context.add_cookies(cookies)

                if stealth_js_path.exists():
                    await context.add_init_script(path=str(stealth_js_path))

                page = await context.new_page()
                await page.goto(DOUYIN_CREATOR_URL, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(3000)

                current_url = page.url
                logger.debug(f"抖音验证当前 URL: {current_url}")

                if current_url.startswith("https://creator.douyin.com/login"):
                    logger.info("抖音 Cookie 无效，被重定向到登录页")
                    return False

                for marker in DOUYIN_LOGIN_MARKERS:
                    try:
                        locator = page.get_by_text(marker, exact=True).first
                        if await locator.count() and await locator.is_visible():
                            logger.info(f"页面显示'{marker}'，Cookie 无效")
                            return False
                    except Exception:
                        pass

                logger.info("抖音 Cookie 有效")
                return True

            finally:
                await browser.close()

    except Exception as e:
        logger.error(f"抖音浏览器验证失败: {e}")
        return False
