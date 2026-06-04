import logging
import random as _random
import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_structure import ContentStructure
from app.models.content_task import ContentTask
from app.models.intent import Intent
from app.models.platform import Platform
from app.services.ai_service import generate_content
from app.services.conversion_service import get_conversion_scripts
from app.utils.time import utc_day_start_naive, utc_now_naive

logger = logging.getLogger(__name__)


FIXED_TEMPLATE = {
    "hook_text": "袜子乱放真的会拖慢出门",
    "storyboard": [
        {"shot": 1, "description": "近景：早上出门翻抽屉找袜子，连续拿出两只不同款，展示真实混乱场景", "duration": "3s", "label": "痛点开场"},
        {"shot": 2, "description": "特写：把起球、袜口松、脚跟磨薄的旧袜子单独挑出来，说明淘汰标准", "duration": "5s", "label": "问题证据"},
        {"shot": 3, "description": "中景：把通勤袜、运动袜、居家袜分成三格，并说明每类适合的鞋型", "duration": "8s", "label": "方法拆解"},
        {"shot": 4, "description": "特写：上脚展示袜口高度、脚跟贴合和鞋内不滑的细节", "duration": "7s", "label": "使用体验"},
        {"shot": 5, "description": "近景：展示整理后的抽屉和当天穿搭，结尾抛出互动问题", "duration": "5s", "label": "互动收尾"},
    ],
    "script_text": "以前我的袜子都是团成一堆，早上越急越找不到。后来我改成按场景分三格：通勤袜放最顺手的位置，运动袜单独一格，居家袜放后排。袜口松了、脚跟磨薄、穿着滑跟的就直接淘汰。这样整理后，黑白灰基础款够日常，彩色款只留真正会搭的，出门不用临时乱翻。",
    "title": "袜子抽屉不乱了｜出门30秒找到一双 #收纳 #袜子搭配",
    "comment_template": "你们袜子最头疼的是滑跟、起球，还是颜色太多不好搭？评论区说下场景，我整理一版清单。",
    "why_it_works": "用真实出门场景切入，先提供收纳和搭配价值，再用低压评论承接需求。",
}


async def generate_task(
    db: AsyncSession,
    user_id: uuid.UUID,
    intent_id: uuid.UUID,
    platform_id: uuid.UUID,
    task_type: str = "video",
    optimization_prompt: str | None = None,
    prev_task_id: uuid.UUID | None = None,
    diagnosis_id: uuid.UUID | None = None,
    skip_pending_check: bool = False,
) -> ContentTask:
    intent_result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = intent_result.scalars().first()
    if not intent or not intent.is_active:
        raise ValueError("Intent not available")

    platform_result = await db.execute(select(Platform).where(Platform.id == platform_id))
    platform = platform_result.scalars().first()
    if not platform or not platform.is_active:
        raise ValueError("Platform not available")

    today_start = utc_day_start_naive()
    if not skip_pending_check:
        existing = await db.execute(
            select(ContentTask).where(
                and_(
                    ContentTask.user_id == user_id,
                    ContentTask.platform_id == platform_id,
                    ContentTask.status.in_(["PENDING", "PUBLISHED"]),
                    ContentTask.created_at >= today_start,
                )
            )
        )
        existing_task = existing.scalars().first()
        if existing_task:
            raise ValueError("HAS_PENDING_TASK")

    structure, market_insights = await match_content_structure(db, intent_id, platform_id)

    conversion_scripts = await get_conversion_scripts(db, intent_id)

    if structure:
        content, is_fallback = await generate_content(
            intent_name=intent.name,
            intent_description=intent.description,
            platform_name=platform.name,
            hook_type=structure.hook_type,
            emotion_structure=structure.emotion_structure,
            conversion_structure=structure.conversion_structure,
            optimization_prompt=optimization_prompt,
            fallback_content=structure.fallback_content,
            task_type=task_type,
            conversion_scripts=conversion_scripts,
            market_insights=market_insights,
        )
    else:
        logger.warning(f"未找到内容结构(intent={intent_id}, platform={platform_id})")
        content = FIXED_TEMPLATE.copy()

    is_optimized = optimization_prompt is not None
    optimization_note = None
    if is_optimized and optimization_prompt:
        hook_desc = structure.hook_type if structure else "默认"
        optimization_note = f"已针对上次问题优化：{optimization_prompt[:50]}。当前使用{hook_desc}结构"

    task = ContentTask(
        user_id=user_id,
        intent_id=intent_id,
        platform_id=platform_id,
        structure_id=structure.id if structure else None,
        status="PENDING",
        task_type=task_type,
        hook_text=content.get("hook_text", FIXED_TEMPLATE["hook_text"]),
        storyboard=content.get("storyboard", FIXED_TEMPLATE["storyboard"]),
        script_text=content.get("script_text", FIXED_TEMPLATE["script_text"]),
        title=content.get("title", FIXED_TEMPLATE["title"]),
        comment_template=content.get("comment_template", FIXED_TEMPLATE["comment_template"]),
        why_it_works=content.get("why_it_works", FIXED_TEMPLATE["why_it_works"]),
        is_optimized=is_optimized,
        optimization_note=optimization_note,
        swap_count=0,
        prev_task_id=prev_task_id,
        diagnosis_id=diagnosis_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def _get_market_insights(db: AsyncSession, platform_id: uuid.UUID) -> dict | None:
    """获取市场热门数据作为 AI 创作参考"""
    from app.models.market_hot import MarketHot

    now = utc_now_naive()
    result = await db.execute(
        select(MarketHot).where(
            MarketHot.platform_id == platform_id,
            MarketHot.is_active.is_(True),
            (MarketHot.expires_at.is_(None)) | (MarketHot.expires_at > now),
        ).order_by(MarketHot.created_at.desc()).limit(5)
    )
    hots = result.scalars().all()

    if not hots:
        return None

    insights = {
        "hot_titles": [],
        "hot_tags": [],
        "emotional_patterns": [],
        "high_engagement_hooks": [],
        "content_themes": [],
        "sentiment_summary": {},
    }

    for hot in hots:
        if hot.analysis_result:
            for key in insights.keys():
                if key in hot.analysis_result and key != "sentiment_summary":
                    insights[key].extend(hot.analysis_result[key])
        if hot.comment_sentiment:
            insights["sentiment_summary"] = hot.comment_sentiment

    for key in ["hot_titles", "hot_tags", "emotional_patterns", "high_engagement_hooks", "content_themes"]:
        insights[key] = list(set(insights[key]))[:10]

    return insights


async def match_content_structure(
    db: AsyncSession,
    intent_id: uuid.UUID,
    platform_id: uuid.UUID,
) -> tuple[ContentStructure | None, dict | None]:
    from app.models.market_hot import MarketHot

    result = await db.execute(
        select(ContentStructure)
        .where(
            ContentStructure.intent_id == intent_id,
            ContentStructure.platform_id == platform_id,
            ContentStructure.is_active.is_(True),
        )
    )
    structures = result.scalars().all()
    if not structures:
        return None, None

    now = utc_now_naive()
    hot_result = await db.execute(
        select(MarketHot).where(
            MarketHot.platform_id == platform_id,
            MarketHot.is_active.is_(True),
            (MarketHot.expires_at.is_(None)) | (MarketHot.expires_at > now),
        )
    )
    active_hots = hot_result.scalars().all()

    boost_map: dict[str, float] = {}
    for hot in active_hots:
        if hot.recommended_structures:
            for struct_name in hot.recommended_structures:
                boost_map[struct_name] = boost_map.get(struct_name, 0.0) + hot.priority_boost

    def _effective_score(s: ContentStructure) -> float:
        boost = boost_map.get(s.hook_type, 0.0)
        return s.priority * 0.6 + (s.market_score + boost) * 0.4

    sorted_structures = sorted(
        structures,
        key=_effective_score,
        reverse=True,
    )
    structure = _random.choice(sorted_structures[:3]) if len(sorted_structures) > 1 else sorted_structures[0]

    market_insights = await _get_market_insights(db, platform_id)

    return structure, market_insights


async def get_current_task(db: AsyncSession, user_id: uuid.UUID, platform_id: uuid.UUID | None = None) -> ContentTask | None:
    query = select(ContentTask).where(
        ContentTask.user_id == user_id,
        ContentTask.status.in_(["PENDING", "PUBLISHED"])
    )
    if platform_id:
        query = query.where(ContentTask.platform_id == platform_id)
    result = await db.execute(
        query.order_by(ContentTask.created_at.desc()).limit(1)
    )
    return result.scalars().first()


async def generate_image_task(
    db: AsyncSession,
    user_id: uuid.UUID,
    intent_id: uuid.UUID,
    platform_id: uuid.UUID,
    optimization_prompt: str | None = None,
    prev_task_id: uuid.UUID | None = None,
    diagnosis_id: uuid.UUID | None = None,
) -> ContentTask:
    return await generate_task(
        db=db,
        user_id=user_id,
        intent_id=intent_id,
        platform_id=platform_id,
        task_type="image",
        optimization_prompt=optimization_prompt,
        prev_task_id=prev_task_id,
        diagnosis_id=diagnosis_id,
    )
