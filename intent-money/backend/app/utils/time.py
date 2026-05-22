from datetime import datetime, timezone


def utc_now_naive() -> datetime:
    """Return UTC now in the naive form SQLite returns through aiosqlite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_day_start_naive() -> datetime:
    now = utc_now_naive()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)
