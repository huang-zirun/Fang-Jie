import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.content_structure import ContentStructure
from app.models.content_task import ContentTask
from app.models.optimization_rule import OptimizationRule
from app.models.user import User
from app.schemas.optimization_rule import (
    OptimizationRuleCreate,
    OptimizationRuleOut,
    OptimizationRuleUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(OptimizationRule).order_by(OptimizationRule.priority.desc())
    )
    return result.scalars().all()


@router.post("/optimization-rules", response_model=OptimizationRuleOut)
async def create_optimization_rule(
    data: OptimizationRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
):
    from app.services.ai_service import BANNED_PHRASES
    return {"banned_phrases": BANNED_PHRASES}


@router.put("/banned-words")
async def update_banned_words(
    banned_phrases: list[str],
    current_user: User = Depends(get_current_user),
):
    from app.services.ai_service import BANNED_PHRASES
    BANNED_PHRASES.clear()
    BANNED_PHRASES.extend(banned_phrases)
    return {"banned_phrases": BANNED_PHRASES}


@router.get("/prompt-templates")
async def get_prompt_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ContentStructure.id, ContentStructure.hook_type, ContentStructure.prompt_template)
    )
    templates = [{"id": str(row.id), "hook_type": row.hook_type, "prompt_template": row.prompt_template} for row in result.all()]
    return {"templates": templates}
