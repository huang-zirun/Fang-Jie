import logging
import random as _random
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_structure import ContentStructure
from app.models.content_task import ContentTask
from app.models.intent import Intent
from app.models.platform import Platform
from app.services.ai_service import generate_content
from app.services.conversion_service import get_conversion_scripts

logger = logging.getLogger(__name__)


FIXED_TEMPLATE = {
    "hook_text": "你穿的袜子可能正在伤害你的脚",
    "storyboard": [
        {"shot": 1, "description": "特写：劣质袜子起球、变形的画面", "duration": "3s"},
        {"shot": 2, "description": "对比：展示我们的袜子弹性和质感", "duration": "5s"},
        {"shot": 3, "description": "近景：穿袜子的脚部舒适展示", "duration": "5s"},
        {"shot": 4, "description": "中景：手持多双袜子展示颜色选择", "duration": "5s"},
        {"shot": 5, "description": "近景：手指指向评论区引导私信", "duration": "2s"},
    ],
    "script_text": "你知道吗？市面上80%的袜子穿一个月就变形起球。我之前也是这样，直到我发现了这款袜子。纯棉面料，弹力不勒脚，穿了三个月还像新的一样。关键是价格，5双只要39块9，比超市便宜一半。想了解的评论区扣1，我私信你。",
    "title": "袜子别乱买！这款穿了3个月还像新的 #好物推荐 #袜子推荐",
    "comment_template": "想要同款袜子的姐妹扣1，我私信发你链接！前10名还有额外优惠哦~",
    "why_it_works": "痛点切入+对比展示+低价诱惑+评论区引导私信，完整转化链路",
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
) -> ContentTask:
    intent_result = await db.execute(select(Intent).where(Intent.id == intent_id))
    intent = intent_result.scalars().first()
    if not intent or not intent.is_active:
        raise ValueError("Intent not available")

    platform_result = await db.execute(select(Platform).where(Platform.id == platform_id))
    platform = platform_result.scalars().first()
    if not platform or not platform.is_active:
        raise ValueError("Platform not available")

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    existing = await db.execute(
        select(ContentTask).where(
            and_(
                ContentTask.user_id == user_id,
                ContentTask.status.in_(["PENDING", "PUBLISHED"]),
                ContentTask.created_at >= today_start,
            )
        )
    )
    existing_task = existing.scalars().first()
    if existing_task:
        raise ValueError("HAS_PENDING_TASK")

    structure = await match_content_structure(db, intent_id, platform_id)

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
        )
    else:
        logger.warning(f"No content structure found for intent={intent_id}, platform={platform_id}")
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


async def match_content_structure(
    db: AsyncSession,
    intent_id: uuid.UUID,
    platform_id: uuid.UUID,
) -> ContentStructure | None:
    from datetime import datetime, timezone

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
        return None

    now = datetime.now(timezone.utc)
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
    return _random.choice(sorted_structures[:3]) if len(sorted_structures) > 1 else sorted_structures[0]


async def get_current_task(db: AsyncSession, user_id: uuid.UUID) -> ContentTask | None:
    result = await db.execute(
        select(ContentTask)
        .where(ContentTask.user_id == user_id, ContentTask.status != "EXPIRED")
        .order_by(ContentTask.created_at.desc())
        .limit(1)
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
