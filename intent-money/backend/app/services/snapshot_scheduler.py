import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory
from app.models.content_task import ContentTask
from app.models.performance_snapshot import PerformanceSnapshot
from app.models.platform import Platform
from app.services.platform_scraper.cdp_browser import CdpBrowser

logger = logging.getLogger(__name__)

FETCH_INTERVAL_HOURS = 2
DEPLOY_WINDOW_DAYS = 30
DEDUP_HOURS = 1


async def _get_browser() -> CdpBrowser | None:
    browser = CdpBrowser(
        host=settings.CDP_DEBUG_HOST,
        port=settings.CDP_DEBUG_PORT,
        scheme=settings.CDP_DEBUG_SCHEME,
    )
    if not await browser.check_health():
        logger.warning("CDP browser not available for scheduled snapshot fetch")
        return None
    return browser


async def _fetch_platform_stats(browser: CdpBrowser, platform_name: str) -> tuple[int, int, int] | None:
    try:
        if "抖音" in platform_name or "douyin" in platform_name.lower():
            return await _fetch_douyin_creator_stats(browser)
        elif "小红书" in platform_name or "xhs" in platform_name.lower() or "xiaohongshu" in platform_name.lower():
            return await _fetch_xhs_creator_stats(browser)
    except Exception as e:
        logger.error(f"Failed to fetch stats for {platform_name}: {e}")
    return None


async def _fetch_douyin_creator_stats(browser: CdpBrowser) -> tuple[int, int, int] | None:
    creator_url = "https://creator.douyin.com/creator-micro/content/manage"
    await browser.navigate(creator_url, wait_seconds=5.0)

    raw = await browser.evaluate("""
    (function() {
        var items = document.querySelectorAll('[class*="content-item"], [class*="video-item"], [class*="work-item"]');
        var result = {play_count: 0, comment_count: 0, message_count: 0};
        if (items.length > 0) {
            var first = items[0];
            var spans = first.querySelectorAll('span, [class*="count"], [class*="num"]');
            var nums = [];
            spans.forEach(function(s) {
                var t = s.textContent.trim();
                if (/^[\\d.]+万?$/.test(t)) nums.push(t);
            });
            if (nums.length >= 1) result.play_count = nums[0];
            if (nums.length >= 2) result.comment_count = nums[1];
        }
        return JSON.stringify(result);
    })()
    """)

    if not raw:
        return None

    import json
    data = json.loads(raw)
    play_count = _parse_count(data.get("play_count", "0"))
    comment_count = _parse_count(data.get("comment_count", "0"))
    message_count = _parse_count(data.get("message_count", "0"))
    return play_count, comment_count, message_count


async def _fetch_xhs_creator_stats(browser: CdpBrowser) -> tuple[int, int, int] | None:
    creator_url = "https://creator.xiaohongshu.com/publish/publish?source=note"
    await browser.navigate(creator_url, wait_seconds=5.0)

    raw = await browser.evaluate("""
    (function() {
        var result = {play_count: 0, comment_count: 0, message_count: 0};
        var items = document.querySelectorAll('[class*="note-item"], [class*="content-item"]');
        if (items.length > 0) {
            var first = items[0];
            var spans = first.querySelectorAll('span, [class*="count"], [class*="num"]');
            var nums = [];
            spans.forEach(function(s) {
                var t = s.textContent.trim();
                if (/^[\\d.]+万?$/.test(t)) nums.push(t);
            });
            if (nums.length >= 1) result.play_count = nums[0];
            if (nums.length >= 2) result.comment_count = nums[1];
        }
        return JSON.stringify(result);
    })()
    """)

    if not raw:
        return None

    import json
    data = json.loads(raw)
    play_count = _parse_count(data.get("play_count", "0"))
    comment_count = _parse_count(data.get("comment_count", "0"))
    message_count = _parse_count(data.get("message_count", "0"))
    return play_count, comment_count, message_count


def _parse_count(value) -> int:
    if isinstance(value, int):
        return value
    if not value:
        return 0
    s = str(value).strip()
    if "万" in s:
        return int(float(s.replace("万", "")) * 10000)
    try:
        return int(s)
    except ValueError:
        return 0


async def scheduled_snapshot_fetch():
    if not settings.CDP_ENABLED:
        logger.debug("CDP not enabled, skipping scheduled snapshot fetch")
        return

    browser = await _get_browser()
    if not browser:
        return

    try:
        async with async_session_factory() as db:
            now = datetime.now(timezone.utc)
            deploy_cutoff = now - timedelta(days=DEPLOY_WINDOW_DAYS)
            dedup_cutoff = now - timedelta(hours=DEDUP_HOURS)

            result = await db.execute(
                select(ContentTask).where(
                    ContentTask.status.in_(["PUBLISHED", "DIAGNOSED"]),
                    ContentTask.deployed_at.isnot(None),
                    ContentTask.deployed_at >= deploy_cutoff,
                )
            )
            tasks = result.scalars().all()

            fetched_count = 0
            for task in tasks:
                recent_snap = await db.execute(
                    select(PerformanceSnapshot).where(
                        PerformanceSnapshot.task_id == task.id,
                        PerformanceSnapshot.source == "cdp_auto",
                        PerformanceSnapshot.snapshot_at >= dedup_cutoff,
                    )
                )
                if recent_snap.scalars().first():
                    continue

                platform_result = await db.execute(
                    select(Platform).where(Platform.id == task.platform_id)
                )
                platform = platform_result.scalars().first()
                if not platform:
                    continue

                stats = await _fetch_platform_stats(browser, platform.name)
                if not stats:
                    continue

                play_count, comment_count, message_count = stats
                snapshot = PerformanceSnapshot(
                    task_id=task.id,
                    play_count=play_count,
                    comment_count=comment_count,
                    message_count=message_count,
                    source="cdp_auto",
                )
                db.add(snapshot)
                fetched_count += 1

            if fetched_count > 0:
                await db.commit()

            logger.info(f"Scheduled snapshot fetch completed: {fetched_count} snapshots created for {len(tasks)} eligible tasks")

    except Exception as e:
        logger.error(f"Scheduled snapshot fetch failed: {e}")
    finally:
        await browser.close()
