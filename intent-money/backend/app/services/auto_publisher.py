"""Auto publisher using sau CLI.

Publishes content to platforms via the social-auto-upload CLI tool.
"""

import asyncio
import logging
import shutil
import uuid
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def _get_sau_path() -> str | None:
    """获取 sau CLI 的路径"""
    if settings.SOCIAL_AUTO_UPLOAD_PATH:
        sau_venv = Path(settings.SOCIAL_AUTO_UPLOAD_PATH) / ".venv" / "Scripts" / "sau.exe"
        if sau_venv.exists():
            return str(sau_venv)

    sau_path = shutil.which("sau")
    if sau_path:
        return sau_path

    return None


def _check_social_auto_upload() -> str | None:
    """检查 social-auto-upload 是否配置正确"""
    if not settings.SOCIAL_AUTO_UPLOAD_PATH:
        return None
    base = Path(settings.SOCIAL_AUTO_UPLOAD_PATH)
    if not base.exists():
        return None
    if not (base / "sau_cli.py").exists():
        return None
    return str(base)


async def _run_sau_command(cmd: list[str]) -> dict:
    """运行 sau 命令并返回结果"""
    task_id = str(uuid.uuid4())

    try:
        logger.info(f"执行sau命令: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

        stdout_str = stdout.decode("utf-8", errors="replace").strip()
        stderr_str = stderr.decode("utf-8", errors="replace").strip()

        if proc.returncode == 0:
            logger.info(f"sau命令执行成功: {stdout_str}")
            return {"success": True, "task_id": task_id, "error": None}
        else:
            err_msg = stderr_str or stdout_str or "未知错误"
            logger.error(f"sau命令执行失败: {err_msg}")
            return {"success": False, "task_id": task_id, "error": err_msg[:500]}

    except asyncio.TimeoutError:
        return {"success": False, "task_id": task_id, "error": "发布超时（300秒）"}
    except FileNotFoundError:
        return {"success": False, "task_id": task_id, "error": "sau 命令未找到，请检查 social-auto-upload 安装"}
    except Exception as e:
        logger.exception("Sau command error")
        return {"success": False, "task_id": task_id, "error": str(e)}


async def publish_to_douyin_sau(
    video_path: str,
    title: str,
    tags: list[str],
    account_name: str,
) -> dict[str, Any]:
    """使用 sau 发布视频到抖音（备用方案）"""
    base_path = _check_social_auto_upload()
    if not base_path:
        return {
            "success": False,
            "task_id": str(uuid.uuid4()),
            "error": "social-auto-upload 未配置或路径不存在，请设置 SOCIAL_AUTO_UPLOAD_PATH",
        }

    sau_path = _get_sau_path()
    if not sau_path:
        return {
            "success": False,
            "task_id": str(uuid.uuid4()),
            "error": "sau CLI 未找到，请检查 social-auto-upload 安装",
        }

    tags_str = ",".join(tags) if tags else ""

    cmd = [
        sau_path,
        "douyin",
        "upload-video",
        "--account", account_name,
        "--file", video_path,
        "--title", title,
        "--desc", title,
    ]

    if tags_str:
        cmd.extend(["--tags", tags_str])

    return await _run_sau_command(cmd)


async def publish_to_xhs_sau(
    image_paths: list[str],
    title: str,
    content: str,
    tags: list[str],
    account_name: str,
) -> dict[str, Any]:
    """使用 sau 发布图文到小红书（备用方案）"""
    base_path = _check_social_auto_upload()
    if not base_path:
        return {
            "success": False,
            "task_id": str(uuid.uuid4()),
            "error": "social-auto-upload 未配置或路径不存在",
        }

    sau_path = _get_sau_path()
    if not sau_path:
        return {
            "success": False,
            "task_id": str(uuid.uuid4()),
            "error": "sau CLI 未找到",
        }

    tags_str = ",".join(tags) if tags else ""

    cmd = [
        sau_path,
        "xiaohongshu",
        "upload-note",
        "--account", account_name,
        "--title", title,
        "--note", content,
        "--images",
    ]
    cmd.extend(image_paths)

    if tags_str:
        cmd.extend(["--tags", tags_str])

    return await _run_sau_command(cmd)


async def publish_xhs_video_sau(
    video_path: str,
    title: str,
    content: str,
    tags: list[str],
    account_name: str,
) -> dict[str, Any]:
    """使用 sau 发布视频到小红书（备用方案）"""
    sau_path = _get_sau_path()
    if not sau_path:
        return {
            "success": False,
            "task_id": str(uuid.uuid4()),
            "error": "sau CLI 未找到",
        }

    tags_str = ",".join(tags) if tags else ""

    cmd = [
        sau_path,
        "xiaohongshu",
        "upload-video",
        "--account", account_name,
        "--file", video_path,
        "--title", title,
        "--desc", content,
    ]

    if tags_str:
        cmd.extend(["--tags", tags_str])

    return await _run_sau_command(cmd)


async def auto_publish_task(
    platform: str,
    user_id: str,
    video_path: str | None = None,
    image_paths: list[str] | None = None,
    title: str = "",
    content: str = "",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """自动发布任务（使用 sau CLI）

    Args:
        platform: 平台名称 (douyin, xhs)
        user_id: 用户ID
        video_path: 视频路径
        image_paths: 图片路径列表
        title: 标题
        content: 内容/描述
        tags: 标签列表
    """
    if not settings.AUTO_PUBLISH_ENABLED:
        return {
            "success": False,
            "task_id": str(uuid.uuid4()),
            "error": "自动发布功能未启用",
        }

    tags = tags or []

    if platform == "douyin":
        if not video_path:
            return {
                "success": False,
                "task_id": str(uuid.uuid4()),
                "error": "抖音发布需要视频文件路径",
            }
        result = await publish_to_douyin_sau(video_path, title, tags, user_id)
        logger.info("抖音发布结果: success=%s", result["success"])
        return result

    elif platform == "xhs":
        if video_path:
            result = await publish_xhs_video_sau(video_path, title, content, tags, user_id)
        elif image_paths:
            result = await publish_to_xhs_sau(image_paths, title, content, tags, user_id)
        else:
            return {
                "success": False,
                "task_id": str(uuid.uuid4()),
                "error": "小红书发布需要视频或图片",
            }
        logger.info("小红书发布结果: success=%s", result["success"])
        return result
    else:
        return {
            "success": False,
            "task_id": str(uuid.uuid4()),
            "error": f"不支持的平台: {platform}",
        }


# 保持向后兼容的别名
publish_to_douyin = publish_to_douyin_sau
publish_to_xhs = publish_to_xhs_sau
