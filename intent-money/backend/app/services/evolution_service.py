import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.optimization_rule import OptimizationRule

logger = logging.getLogger(__name__)


async def adjust_rule_weights(db: AsyncSession) -> dict:
    result = await db.execute(
        select(OptimizationRule).where(OptimizationRule.is_active.is_(True))
    )
    rules = result.scalars().all()

    adjusted = []
    for rule in rules:
        if rule.hit_count == 0:
            adjusted.append({
                "rule_id": str(rule.id),
                "name": rule.name,
                "hit_count": 0,
                "accuracy_count": 0,
                "accuracy_rate": None,
                "old_priority": rule.priority,
                "new_priority": rule.priority,
                "action": "skip",
            })
            continue

        accuracy_rate = rule.accuracy_count / rule.hit_count

        old_priority = rule.priority
        action = "keep"

        if accuracy_rate > 0.7:
            new_priority = min(rule.priority + 5, 200)
            if new_priority != rule.priority:
                rule.priority = new_priority
                action = "boost"
        elif accuracy_rate < 0.4 and rule.hit_count >= 5:
            new_priority = max(rule.priority - 5, 10)
            if new_priority != rule.priority:
                rule.priority = new_priority
                action = "reduce"

        adjusted.append({
            "rule_id": str(rule.id),
            "name": rule.name,
            "hit_count": rule.hit_count,
            "accuracy_count": rule.accuracy_count,
            "accuracy_rate": round(accuracy_rate, 4),
            "old_priority": old_priority,
            "new_priority": rule.priority,
            "action": action,
        })

    await db.commit()

    logger.info(f"Rule weight adjustment completed: {len(adjusted)} rules processed")

    return {
        "total_rules": len(adjusted),
        "adjustments": adjusted,
    }
