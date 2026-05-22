import asyncio
import logging
import uuid
from pathlib import Path

from app.config import settings
from app.services.cookie_manager import get_cookie_path

logger = logging.getLogger(__name__)


def _check_social_auto_upload() -> str | None:
    if not settings.SOCIAL_AUTO_UPLOAD_PATH:
        return None
    base = Path(settings.SOCIAL_AUTO_UPLOAD_PATH)
    if not base.exists():
        return None
    return str(base)


async def publish_to_douyin(
    video_path: str,
    title: str,
    tags: list[str],
    cookie_path: str,
) -> dict:
    task_id = str(uuid.uuid4())
    base_path = _check_social_auto_upload()
    if not base_path:
        return {
            "success": False,
            "task_id": task_id,
            "error": "social-auto-upload 未配置或路径不存在，请设置 SOCIAL_AUTO_UPLOAD_PATH",
        }

    script_path = Path(base_path) / "upload_douyin.py"
    if not script_path.exists():
        return {
            "success": False,
            "task_id": task_id,
            "error": f"抖音上传脚本不存在: {script_path}",
        }

    tags_str = " ".join(f"#{t}" for t in tags)
    cmd = [
        "python", str(script_path),
        "--video", video_path,
        "--title", title,
        "--tags", tags_str,
        "--cookie", cookie_path,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

        if proc.returncode == 0:
            return {"success": True, "task_id": task_id, "error": None}
        else:
            err_msg = stderr.decode("utf-8", errors="replace").strip()[:500]
            logger.error(f"Douyin publish failed: {err_msg}")
            return {"success": False, "task_id": task_id, "error": err_msg}
    except asyncio.TimeoutError:
        return {"success": False, "task_id": task_id, "error": "发布超时（300秒）"}
    except FileNotFoundError:
        return {"success": False, "task_id": task_id, "error": "Python 环境未找到，无法执行上传脚本"}
    except Exception as e:
        logger.exception("Douyin publish error")
        return {"success": False, "task_id": task_id, "error": str(e)}


async def publish_to_xhs(
    image_paths: list[str],
    title: str,
    content: str,
    tags: list[str],
    cookie_path: str,
) -> dict:
    task_id = str(uuid.uuid4())
    base_path = _check_social_auto_upload()
    if not base_path:
        return {
            "success": False,
            "task_id": task_id,
            "error": "social-auto-upload 未配置或路径不存在，请设置 SOCIAL_AUTO_UPLOAD_PATH",
        }

    script_path = Path(base_path) / "upload_xhs.py"
    if not script_path.exists():
        return {
            "success": False,
            "task_id": task_id,
            "error": f"小红书上传脚本不存在: {script_path}",
        }

    tags_str = " ".join(f"#{t}" for t in tags)
    images_str = ",".join(image_paths)
    cmd = [
        "python", str(script_path),
        "--images", images_str,
        "--title", title,
        "--content", content,
        "--tags", tags_str,
        "--cookie", cookie_path,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

        if proc.returncode == 0:
            return {"success": True, "task_id": task_id, "error": None}
        else:
            err_msg = stderr.decode("utf-8", errors="replace").strip()[:500]
            logger.error(f"XHS publish failed: {err_msg}")
            return {"success": False, "task_id": task_id, "error": err_msg}
    except asyncio.TimeoutError:
        return {"success": False, "task_id": task_id, "error": "发布超时（300秒）"}
    except FileNotFoundError:
        return {"success": False, "task_id": task_id, "error": "Python 环境未找到，无法执行上传脚本"}
    except Exception as e:
        logger.exception("XHS publish error")
        return {"success": False, "task_id": task_id, "error": str(e)}


async def auto_publish_task(
    platform: str,
    user_id: str,
    video_path: str | None = None,
    image_paths: list[str] | None = None,
    title: str = "",
    content: str = "",
    tags: list[str] | None = None,
) -> dict:
    if not settings.AUTO_PUBLISH_ENABLED:
        return {
            "success": False,
            "task_id": str(uuid.uuid4()),
            "error": "自动发布功能未启用",
        }

    tags = tags or []
    cookie_path = await get_cookie_path(platform, user_id)
    if not cookie_path:
        return {
            "success": False,
            "task_id": str(uuid.uuid4()),
            "error": f"未找到 {platform} 的 Cookie，请先上传",
        }

    if platform == "douyin":
        if not video_path:
            return {
                "success": False,
                "task_id": str(uuid.uuid4()),
                "error": "抖音发布需要视频文件路径",
            }
        return await publish_to_douyin(video_path, title, tags, cookie_path)
    elif platform == "xhs":
        if not image_paths:
            return {
                "success": False,
                "task_id": str(uuid.uuid4()),
                "error": "小红书发布需要图片文件路径",
            }
        return await publish_to_xhs(image_paths, title, content, tags, cookie_path)
    else:
        return {
            "success": False,
            "task_id": str(uuid.uuid4()),
            "error": f"不支持的平台: {platform}",
        }
