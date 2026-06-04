import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

XHS_LOGIN_URL = "https://creator.xiaohongshu.com/login"
XHS_PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=video"
XHS_PROFILE_URL = "https://www.xiaohongshu.com/user/profile/"


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
            "domain": ".xiaohongshu.com",
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


async def validate_xhs_cookie(cookie_data: str) -> bool:
    """
    验证小红书 Cookie 有效性

    支持两种格式：
    1. storage_state JSON（扫码登录保存的格式）
    2. Cookie 字符串（手动导入的格式）

    使用 Playwright 浏览器验证：
    1. 启动浏览器，注入 stealth 脚本
    2. 加载 Cookie / storage_state
    3. 访问小红书创作者中心
    4. 检查是否被重定向到登录页
    """
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
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-site-isolated-trials",
                ],
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
                
                # 第一次尝试：访问创作者中心发布页
                logger.info("开始验证Cookie有效性，尝试访问创作者中心发布页...")
                try:
                    await page.goto(XHS_PUBLISH_URL, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(5000)
                    
                    current_url = page.url
                    logger.info(f"创作者中心当前 URL: {current_url}")
                    
                    # 检查是否被重定向到登录页
                    if current_url.startswith(XHS_LOGIN_URL):
                        logger.info("创作者中心被重定向到登录页，尝试访问个人主页...")
                    else:
                        # 检查登录框
                        login_box = page.locator("div[class*='login-box']").first
                        if await login_box.count():
                            try:
                                if await login_box.is_visible():
                                    logger.info("创作者中心显示登录框，尝试访问个人主页...")
                                else:
                                    logger.info("Cookie有效，成功访问创作者中心")
                                    return True
                            except Exception:
                                logger.info("Cookie有效，成功访问创作者中心")
                                return True
                        else:
                            logger.info("Cookie有效，成功访问创作者中心")
                            return True
                except Exception as e:
                    logger.warning(f"访问创作者中心失败: {e}，尝试访问个人主页...")
                
                # 第二次尝试：访问个人主页
                logger.info("开始尝试访问个人主页...")
                try:
                    await page.goto(XHS_PROFILE_URL, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(5000)
                    
                    current_url = page.url
                    logger.info(f"个人主页当前 URL: {current_url}")
                    
                    # 检查是否被重定向到登录页
                    if "login" in current_url.lower() or "signin" in current_url.lower():
                        logger.info("个人主页被重定向到登录页，Cookie无效")
                        return False
                    
                    # 检查是否有登录按钮或登录框
                    login_indicators = [
                        page.locator("div[class*='login-box']").first,
                        page.locator("button[class*='login']").first,
                        page.locator("a[href*='login']").first,
                    ]
                    
                    for indicator in login_indicators:
                        if await indicator.count():
                            try:
                                if await indicator.is_visible():
                                    logger.info("个人主页显示登录相关元素，Cookie无效")
                                    return False
                            except Exception:
                                pass
                    
                    logger.info("Cookie有效，成功访问个人主页")
                    return True
                    
                except Exception as e:
                    logger.error(f"访问个人主页失败: {e}")
                    return False

            finally:
                await browser.close()

    except Exception as e:
        logger.error(f"浏览器验证失败: {e}")
        return False
