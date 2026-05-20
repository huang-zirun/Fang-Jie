import json
import logging
import time

from openai import APIError, APITimeoutError, AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

BANNED_PHRASES = [
    "最便宜", "全网最低", "最低价", "史上最低", "绝对",
    "月入过万", "日赚千元", "轻松赚钱", "躺赚",
    "治疗", "治愈", "疗效", "药效", "处方",
]

TASK_OUTPUT_SCHEMA = {
    "hook_text": {"type": "string", "max_length": 30, "required": True},
    "storyboard": {"type": "list", "min_items": 3, "max_items": 5, "required": True},
    "script_text": {"type": "string", "min_length": 50, "max_length": 300, "required": True},
    "title": {"type": "string", "max_length": 50, "required": True},
    "comment_template": {"type": "string", "required": True},
    "why_it_works": {"type": "string", "required": True},
}


def _build_prompt(
    intent_name: str,
    intent_description: str,
    platform_name: str,
    hook_type: str,
    emotion_structure: dict,
    conversion_structure: dict,
    optimization_prompt: str | None = None,
    task_type: str = "video",
) -> str:
    parts = [
        "你是一名袜子分销内容策划专家。",
        "",
        "## 任务",
        "基于以下内容结构模板，生成一条完整的短视频内容任务。" if task_type == "video" else "基于以下内容结构模板，生成一条完整的图文笔记内容任务。",
        "",
        "## 用户意图",
        f"{intent_name}：{intent_description}",
        "",
        "## 发布平台",
        platform_name,
        "",
        "## 产品类型",
        "袜子（分销模式）",
        "",
        "## 内容形式",
        "图文笔记（图片+文案，无需拍摄视频）" if task_type == "image" else "短视频（需要拍摄）",
        "",
        "## 目标人群",
        "对袜子有需求的普通消费者，尤其是注重性价比和实用性的群体",
        "",
        "## 内容结构模板",
        f"- 钩子类型：{hook_type}",
        f"- 情绪结构：{json.dumps(emotion_structure, ensure_ascii=False)}",
        f"- 转化结构：{json.dumps(conversion_structure, ensure_ascii=False)}",
    ]

    if optimization_prompt:
        parts.extend([
            "",
            "## 优化约束",
            optimization_prompt,
        ])

    if task_type == "image":
        storyboard_example = [
            {"shot": 1, "description": "图片描述", "label": "产品展示"},
            {"shot": 2, "description": "图片描述", "label": "对比效果"},
            {"shot": 3, "description": "图片描述", "label": "使用场景"}
        ]
    else:
        storyboard_example = [
            {"shot": 1, "description": "镜头描述", "duration": "3s"},
            {"shot": 2, "description": "镜头描述", "duration": "5s"},
            {"shot": 3, "description": "镜头描述", "duration": "10s"}
        ]

    parts.extend([
        "",
        "## 禁用表达",
        "- 不得出现「最便宜」「全网最低」等绝对化用语",
        "- 不得出现医疗功效承诺",
        "- 不得出现虚假收益承诺",
        "- 不得出现「月入过万」等夸大宣传",
        "",
        "## 输出格式（严格 JSON）",
        "```json",
        json.dumps({
            "hook_text": "3秒钩子文案，15字以内",
            "storyboard": storyboard_example,
            "script_text": "完整口播文案，100-200字",
            "title": "发布标题，含2-3个话题标签",
            "comment_template": "评论区置顶话术，引导私信或互动",
            "why_it_works": "一句话说明为什么这条内容能赚钱"
        }, ensure_ascii=False, indent=2),
        "```",
    ])

    return "\n".join(parts)


def _validate_output(data: dict) -> list[str]:
    errors = []

    if not data.get("hook_text") or len(data["hook_text"]) > 30:
        errors.append("hook_text invalid")

    storyboard = data.get("storyboard", [])
    if not isinstance(storyboard, list) or len(storyboard) < 3 or len(storyboard) > 5:
        errors.append("storyboard invalid")

    script = data.get("script_text", "")
    if not script or len(script) < 50 or len(script) > 300:
        errors.append("script_text invalid")

    if not data.get("title") or len(data["title"]) > 50:
        errors.append("title invalid")

    if not data.get("comment_template"):
        errors.append("comment_template invalid")

    if not data.get("why_it_works"):
        errors.append("why_it_works invalid")

    all_text = " ".join(str(v) for v in data.values() if isinstance(v, str))
    for phrase in BANNED_PHRASES:
        if phrase in all_text:
            errors.append(f"banned phrase: {phrase}")

    if "袜子" not in all_text and "袜" not in all_text:
        errors.append("missing product keyword")

    return errors


async def generate_content(
    intent_name: str,
    intent_description: str,
    platform_name: str,
    hook_type: str,
    emotion_structure: dict,
    conversion_structure: dict,
    optimization_prompt: str | None = None,
    fallback_content: dict | None = None,
    task_type: str = "video",
) -> tuple[dict, bool]:
    prompt = _build_prompt(
        intent_name=intent_name,
        intent_description=intent_description,
        platform_name=platform_name,
        hook_type=hook_type,
        emotion_structure=emotion_structure,
        conversion_structure=conversion_structure,
        optimization_prompt=optimization_prompt,
        task_type=task_type,
    )

    if not settings.AI_API_KEY:
        logger.warning("AI_API_KEY not set, using fallback")
        return fallback_content or {}, True

    client = AsyncOpenAI(
        api_key=settings.AI_API_KEY,
        base_url=settings.AI_BASE_URL,
    )

    for attempt in range(2):
        start_time = time.time()
        try:
            response = await client.chat.completions.create(
                model=settings.AI_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                timeout=10.0,
            )

            elapsed = time.time() - start_time

            text = response.choices[0].message.content or ""

            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            data = json.loads(text.strip())

            errors = _validate_output(data)
            if errors:
                logger.warning(f"AI output validation failed (attempt {attempt + 1}): {errors}")
                if attempt == 0:
                    continue
                return fallback_content or {}, True

            usage = response.usage
            logger.info(
                f"AI generation succeeded in {elapsed:.2f}s, "
                f"input_tokens={usage.prompt_tokens if usage else 0}, "
                f"output_tokens={usage.completion_tokens if usage else 0}"
            )
            return data, False

        except APITimeoutError:
            logger.warning(f"AI timeout (attempt {attempt + 1})")
            if attempt == 0:
                continue
        except APIError as e:
            logger.error(f"AI API error: {e}")
            if attempt == 0:
                continue
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"AI output parse error (attempt {attempt + 1}): {e}")
            if attempt == 0:
                continue

    logger.warning("All AI attempts failed, using fallback")
    return fallback_content or {}, True
