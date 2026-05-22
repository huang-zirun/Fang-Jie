import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.content_structure import ContentStructure
from app.models.content_task import ContentTask
from app.models.market_hot import MarketHot
from app.models.optimization_rule import OptimizationRule
from app.models.user import User
from app.schemas.content_structure import (
    ContentStructureCreate,
    ContentStructureOut,
)
from app.schemas.optimization_rule import (
    OptimizationRuleCreate,
    OptimizationRuleOut,
    OptimizationRuleUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    total_users = await db.scalar(select(func.count(User.id)))
    total_tasks = await db.scalar(select(func.count(ContentTask.id)))
    published_tasks = await db.scalar(
        select(func.count(ContentTask.id)).where(ContentTask.status.in_(["PUBLISHED", "REPORTED", "DIAGNOSED"]))
    )
    reported_tasks = await db.scalar(
        select(func.count(ContentTask.id)).where(ContentTask.status.in_(["REPORTED", "DIAGNOSED"]))
    )

    publish_rate = (published_tasks / total_tasks * 100) if total_tasks and total_tasks > 0 else 0
    report_rate = (reported_tasks / published_tasks * 100) if published_tasks and published_tasks > 0 else 0

    return {
        "total_users": total_users or 0,
        "total_tasks": total_tasks or 0,
        "published_tasks": published_tasks or 0,
        "reported_tasks": reported_tasks or 0,
        "publish_rate": round(publish_rate, 1),
        "report_rate": round(report_rate, 1),
    }


@router.get("/optimization-rules", response_model=list[OptimizationRuleOut])
async def list_optimization_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(OptimizationRule).order_by(OptimizationRule.priority.desc())
    )
    return result.scalars().all()


@router.post("/optimization-rules", response_model=OptimizationRuleOut)
async def create_optimization_rule(
    data: OptimizationRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    rule = OptimizationRule(**data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.put("/optimization-rules/{rule_id}", response_model=OptimizationRuleOut)
async def update_optimization_rule(
    rule_id: uuid.UUID,
    data: OptimizationRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(OptimizationRule).where(OptimizationRule.id == rule_id)
    )
    rule = result.scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/optimization-rules/{rule_id}", status_code=204)
async def delete_optimization_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(OptimizationRule).where(OptimizationRule.id == rule_id)
    )
    rule = result.scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()


@router.get("/banned-words")
async def get_banned_words(
    current_user: User = Depends(require_admin),
):
    from app.services.ai_service import BANNED_PHRASES
    return {"banned_phrases": BANNED_PHRASES}


@router.put("/banned-words")
async def update_banned_words(
    banned_phrases: list[str],
    current_user: User = Depends(require_admin),
):
    from app.services.ai_service import BANNED_PHRASES
    BANNED_PHRASES.clear()
    BANNED_PHRASES.extend(banned_phrases)
    return {"banned_phrases": BANNED_PHRASES}


@router.get("/prompt-templates")
async def get_prompt_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(ContentStructure.id, ContentStructure.hook_type, ContentStructure.prompt_template)
    )
    templates = [{"id": str(row.id), "hook_type": row.hook_type, "prompt_template": row.prompt_template} for row in result.all()]
    return {"templates": templates}


@router.post("/content-structures/batch", response_model=list[ContentStructureOut])
async def batch_create_content_structures(
    items: list[ContentStructureCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    structures = []
    for item in items:
        structure = ContentStructure(**item.model_dump(), is_active=True)
        db.add(structure)
        structures.append(structure)
    await db.commit()
    for s in structures:
        await db.refresh(s)
    return structures


@router.post("/evolution/adjust-weights")
async def trigger_adjust_weights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    from app.services.evolution_service import adjust_rule_weights
    result = await adjust_rule_weights(db)
    return result


@router.get("/evolution/stats")
async def get_evolution_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(OptimizationRule).order_by(OptimizationRule.priority.desc())
    )
    rules = result.scalars().all()

    stats = []
    for rule in rules:
        accuracy_rate = None
        if rule.hit_count > 0:
            accuracy_rate = round(rule.accuracy_count / rule.hit_count, 4)
        stats.append({
            "rule_id": str(rule.id),
            "name": rule.name,
            "problem_type": rule.problem_type,
            "hit_count": rule.hit_count,
            "accuracy_count": rule.accuracy_count,
            "accuracy_rate": accuracy_rate,
            "priority": rule.priority,
        })

    return {"stats": stats}


@router.get("/sentiment-summary")
async def get_sentiment_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(MarketHot).where(
            MarketHot.is_active.is_(True),
            MarketHot.comment_sentiment.isnot(None),
        )
    )
    hots = result.scalars().all()

    platform_summary: dict[str, dict] = {}
    overall_positive = 0
    overall_neutral = 0
    overall_negative = 0
    overall_total = 0

    for hot in hots:
        sentiment = hot.comment_sentiment
        if not sentiment:
            continue

        platform_name = hot.platform.name if hot.platform else "unknown"

        if platform_name not in platform_summary:
            platform_summary[platform_name] = {
                "total": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "avg_score": 0.0,
                "score_sum": 0.0,
                "count": 0,
            }

        s = platform_summary[platform_name]
        s["total"] += sentiment.get("total", 0)
        s["positive"] += sentiment.get("positive", 0)
        s["neutral"] += sentiment.get("neutral", 0)
        s["negative"] += sentiment.get("negative", 0)
        s["score_sum"] += sentiment.get("avg_score", 0.0)
        s["count"] += 1

        overall_positive += sentiment.get("positive", 0)
        overall_neutral += sentiment.get("neutral", 0)
        overall_negative += sentiment.get("negative", 0)
        overall_total += sentiment.get("total", 0)

    for name, s in platform_summary.items():
        s["avg_score"] = round(s["score_sum"] / s["count"], 4) if s["count"] > 0 else 0.0
        del s["score_sum"]
        del s["count"]

    overall_avg = 0.0
    if overall_total > 0:
        overall_avg = round(
            (overall_positive * 1.0 + overall_neutral * 0.5 + overall_negative * 0.0) / overall_total,
            4,
        )

    return {
        "platforms": platform_summary,
        "overall": {
            "total": overall_total,
            "positive": overall_positive,
            "neutral": overall_neutral,
            "negative": overall_negative,
            "avg_score": overall_avg,
        },
    }
