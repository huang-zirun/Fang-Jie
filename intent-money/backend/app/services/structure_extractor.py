import json
import logging
import re

from openai import APIError, APITimeoutError, AsyncOpenAI

from app.config import settings
from app.services.platform_scraper import douyin_scraper
from app.services.platform_scraper.xhs_scraper import XhsScraper

logger = logging.getLogger(__name__)

PLATFORM_MAP = {
    "douyin": "抖音",
    "xhs": "小红书",
}


async def _fetch_content_metadata(url: str, platform: str) -> dict | None:
    try:
        if platform == "douyin":
            video_id_match = re.search(r"/video/(\d+)", url)
            if not video_id_match:
                video_id_match = re.search(r"modal_id=(\d+)", url)
            if video_id_match:
                video_id = video_id_match.group(1)
                detail = await douyin_scraper.get_video_detail(video_id)
                if detail:
                    return {
                        "type": "video",
                        "title": detail.get("title", ""),
                        "tags": detail.get("tags", []),
                        "statistics": detail.get("statistics", {}),
                        "author": detail.get("author", {}),
                    }
            return None

        if platform == "xhs":
            note_id_match = re.search(r"/explore/([a-f0-9]+)", url)
            if not note_id_match:
                note_id_match = re.search(r"/discovery/item/([a-f0-9]+)", url)
            if not note_id_match:
                note_id_match = re.search(r"xhslink\.com/(\w+)", url)
            if note_id_match:
                note_id = note_id_match.group(1)
                scraper = XhsScraper()
                detail = await scraper.get_note_detail(note_id)
                if detail:
                    return {
                        "type": "note",
                        "title": detail.get("title", ""),
                        "desc": detail.get("desc", ""),
                        "tags": detail.get("tag_list", []),
                        "liked_count": detail.get("liked_count", "0"),
                        "collected_count": detail.get("collected_count", "0"),
                        "comment_count": detail.get("comment_count", "0"),
                        "author": detail.get("author", ""),
                    }
            return None
    except Exception as e:
        logger.error(f"获取内容元数据失败({url}): {e}")
        return None

    return None


def _build_extraction_prompt(platform_name: str, url: str, metadata: dict | None) -> str:
    metadata_section = ""
    if metadata:
        metadata_section = f"""
## 已获取的内容元数据
{json.dumps(metadata, ensure_ascii=False, indent=2)}
"""
    else:
        metadata_section = """
## 内容元数据
未能自动获取元数据，请根据URL和平台特征进行分析。
"""

    return f"""你是一名短视频/笔记爆款内容结构分析专家，专注于电商类目（特别是袜子类目）。

## 任务
分析以下{platform_name}平台爆款内容的结构，提取其钩子类型、情绪结构、转化信号和爆款要素。

## 内容来源
平台：{platform_name}
URL：{url}
{metadata_section}

## 分析维度
1. **钩子类型**：开头3秒用了什么钩子吸引注意力？（如：痛点型、反常识型、身份识别型、场景切入型、紧迫型、对比型、收益型、低门槛型、裂变型、副业型、分享型、人设型、专业型、故事型、生活方式型、干货型、测评型、套餐型等）
2. **情绪结构**：内容如何调动观众情绪？情绪走向是什么？
3. **转化结构**：如何引导用户从观看到互动到转化？转化路径是什么？
4. **关键要素**：哪些具体技巧让这条内容成为爆款？
5. **爆款潜力评分**：基于结构完整度、情绪强度、转化清晰度打分（0-100）

## 输出格式（严格 JSON）
{{
    "hook_type": "钩子类型名称",
    "emotion_structure": {{
        "type": "情绪结构类型英文标识",
        "flow": "情绪走向描述，用 → 连接各阶段"
    }},
    "conversion_structure": {{
        "type": "转化结构类型英文标识",
        "flow": "转化路径描述，用 → 连接各阶段"
    }},
    "key_elements": ["关键要素1", "关键要素2", "关键要素3"],
    "viral_score": 85,
    "analysis_summary": "200字以内的分析摘要，说明为什么这个结构有效"
}}"""


def _default_extraction() -> dict:
    return {
        "hook_type": "未知型",
        "emotion_structure": {"type": "unknown", "flow": "无法分析"},
        "conversion_structure": {"type": "unknown", "flow": "无法分析"},
        "key_elements": [],
        "viral_score": 0,
        "analysis_summary": "AI分析暂时不可用，请稍后重试",
    }


async def extract_structure_from_url(url: str, platform: str) -> dict | None:
    try:
        platform_name = PLATFORM_MAP.get(platform, platform)

        metadata = await _fetch_content_metadata(url, platform)

        if not settings.AI_API_KEY:
            logger.warning("AI密钥未配置，返回默认提取")
            return _default_extraction()

        prompt = _build_extraction_prompt(platform_name, url, metadata)

        client = AsyncOpenAI(
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_BASE_URL,
        )

        for attempt in range(2):
            try:
                response = await client.chat.completions.create(
                    model=settings.AI_MODEL,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=15.0,
                )

                text = response.choices[0].message.content or ""

                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]

                data = json.loads(text.strip())

                if not isinstance(data, dict) or "hook_type" not in data:
                    logger.warning(f"AI输出结构无效(第{attempt + 1}次)")
                    if attempt == 0:
                        continue
                    return _default_extraction()

                data["viral_score"] = max(0, min(100, int(data.get("viral_score", 0))))

                return data

            except APITimeoutError:
                logger.warning(f"AI超时(第{attempt + 1}次)")
                if attempt == 0:
                    continue
            except APIError as e:
                logger.error(f"AI请求失败: {e}")
                if attempt == 0:
                    continue
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logger.warning(f"AI解析失败(第{attempt + 1}次): {e}")
                if attempt == 0:
                    continue

        logger.warning("AI全部重试失败，返回默认提取")
        return _default_extraction()

    except Exception as e:
        logger.error(f"内容结构提取失败: {e}")
        return None
