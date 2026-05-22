import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


def _cookie_dir() -> Path:
    base = Path(__file__).resolve().parent.parent.parent
    cookie_path = base / settings.COOKIE_DIR
    cookie_path.mkdir(parents=True, exist_ok=True)
    return cookie_path


def _cookie_file_path(platform: str, user_id: str) -> Path:
    return _cookie_dir() / f"{platform}_{user_id}.json"


async def save_cookie(platform: str, user_id: str, cookie_data: str) -> str:
    path = _cookie_file_path(platform, user_id)
    try:
        json.loads(cookie_data)
    except json.JSONDecodeError:
        cookie_data = json.dumps({"raw": cookie_data})
    path.write_text(cookie_data, encoding="utf-8")
    logger.info(f"Cookie saved: {platform}_{user_id}")
    return str(path)


async def get_cookie_path(platform: str, user_id: str) -> str | None:
    path = _cookie_file_path(platform, user_id)
    if path.exists():
        return str(path)
    return None


async def is_cookie_valid(platform: str, user_id: str) -> bool:
    path = _cookie_file_path(platform, user_id)
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    expires_at = mtime + timedelta(days=settings.COOKIE_EXPIRE_DAYS)
    return datetime.now(timezone.utc) < expires_at


async def get_cookie_expires_at(platform: str, user_id: str) -> str | None:
    path = _cookie_file_path(platform, user_id)
    if not path.exists():
        return None
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    expires_at = mtime + timedelta(days=settings.COOKIE_EXPIRE_DAYS)
    return expires_at.isoformat()
