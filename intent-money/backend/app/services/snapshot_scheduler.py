import logging

logger = logging.getLogger(__name__)

FETCH_INTERVAL_HOURS = 2


async def scheduled_snapshot_fetch():
    """Scheduled snapshot fetch - currently disabled.

    Snapshot data should be manually submitted via the API.
    """
    logger.debug("定时快照已跳过，请手动提交")
