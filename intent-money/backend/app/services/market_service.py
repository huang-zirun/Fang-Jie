import json
import logging
import uuid

from openai import APIError, APITimeoutError, AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.content_structure import ContentStructure
from app.models.market_hot import MarketHot
from app.models.platform import Platform

logger = logging.getLogger(__name__)


async def analyze_market_trend(db: AsyncSession, platform_id: uuid.UUID) -> dict:
    platform_result = await db.execute(select(Platform).where(Platform.id == platform_id))
    platform = platform_result.scalars().first()
    if not platform:
        raise ValueError("Platform not found")

    now_result = await db.execute(
        select(MarketHot).where(
            MarketHot.platform_id == platform_id,
            MarketHot.is_active.is_(True),
        )
    )
    active_hots = now_result.scalars().all()

    keywords = [h.keyword for h in active_hots]

    struct_result = await db.execute(
        select(ContentStructure).where(
            ContentStructure.platform_id == platform_id,
            ContentStructure.is_active.is_(True),
        )
    )
    structures = struct_result.scalars().all()
    available_hook_types = list({s.hook_type for s in structures})

    if not settings.AI_API_KEY:
        logger.warning("AI_API_KEY not set, returning default analysis")
        return {
            "summary": "AI未配置，无法分析市场趋势",
            "trending_structures": available_hook_types[:2],
            "suggested_hooks": available_hook_types[:2],
            "priority_adjustments": [],
        }

    prompt = _build_analysis_prompt(platform.name, keywords, available_hook_types)

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

            if not isinstance(data, dict) or "summary" not in data:
                logger.warning(f"AI output invalid structure (attempt {attempt + 1})")
                if attempt == 0:
                    continue
                return _default_analysis(available_hook_types)

            return data

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

    logger.warning("All AI attempts failed, returning default analysis")
    return _default_analysis(available_hook_types)


def _build_analysis_prompt(platform_name: str, keywords: list[str], available_hook_types: list[str]) -> str:
    keywords_text = "\n".join(f"- {k}" for k in keywords) if keywords else "- 暂无热点关键词"
    hook_types_text = "、".join(available_hook_types) if available_hook_types else "暂无"

    return f"""你是一名袜子类目内容运营专家。

## 任务
分析当前{platform_name}平台上袜子类目的内容趋势，推荐最优内容结构。

## 当前热点关键词
{keywords_text}

## 可用内容结构类型
{hook_types_text}

## 输出格式（严格 JSON）
{{
    "summary": "当前市场趋势分析摘要",
    "trending_structures": ["推荐的结构类型1", "推荐的结构类型2"],
    "suggested_hooks": ["推荐的钩子类型1", "推荐的钩子类型2"],
    "priority_adjustments": [
        {{"hook_type": "对比型", "boost": 20}},
        {{"hook_type": "痛点型", "boost": 10}}
    ]
}}"""


def _default_analysis(available_hook_types: list[str]) -> dict:
    return {
        "summary": "AI分析暂时不可用",
        "trending_structures": available_hook_types[:2],
        "suggested_hooks": available_hook_types[:2],
        "priority_adjustments": [],
    }


async def update_market_scores(db: AsyncSession) -> int:
    result = await db.execute(
        select(MarketHot).where(
            MarketHot.is_active.is_(True),
        )
    )
    active_hots = result.scalars().all()

    if not active_hots:
        return 0

    platform_ids = list({h.platform_id for h in active_hots})
    updated_count = 0

    for pid in platform_ids:
        struct_result = await db.execute(
            select(ContentStructure).where(
                ContentStructure.platform_id == pid,
                ContentStructure.is_active.is_(True),
            )
        )
        structures = struct_result.scalars().all()

        platform_hots = [h for h in active_hots if h.platform_id == pid]

        boost_map: dict[str, float] = {}
        for hot in platform_hots:
            if hot.recommended_structures:
                for struct_name in hot.recommended_structures:
                    boost_map[struct_name] = boost_map.get(struct_name, 0.0) + hot.priority_boost

        for struct in structures:
            boost = boost_map.get(struct.hook_type, 0.0)
            if boost != 0.0:
                struct.market_score = struct.market_score + boost
                updated_count += 1

    await db.commit()
    return updated_count
