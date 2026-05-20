import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diagnosis_result import DiagnosisResult
from app.models.optimization_rule import OptimizationRule
from app.models.performance_report import PerformanceReport

logger = logging.getLogger(__name__)


def _evaluate_condition(condition: dict, play_count: int, comment_count: int, message_count: int) -> bool:
    if "and" in condition:
        return all(
            _evaluate_condition(sub, play_count, comment_count, message_count)
            for sub in condition["and"]
        )

    field_map = {
        "play_count": play_count,
        "comment_count": comment_count,
        "message_count": message_count,
    }

    field = condition.get("field")
    operator = condition.get("operator")
    value = condition.get("value")

    actual = field_map.get(field)
    if actual is None:
        return False

    if operator == "lt":
        return actual < value
    elif operator == "lte":
        return actual <= value
    elif operator == "gt":
        return actual > value
    elif operator == "gte":
        return actual >= value
    elif operator == "eq":
        return actual == value
    elif operator == "ne":
        return actual != value

    return False


async def diagnose_performance(
    db: AsyncSession,
    report: PerformanceReport,
) -> DiagnosisResult:
    result = await db.execute(
        select(OptimizationRule)
        .where(OptimizationRule.is_active == True)
        .order_by(OptimizationRule.priority.desc())
    )
    rules = result.scalars().all()

    matched_rule = None
    for rule in rules:
        if _evaluate_condition(
            rule.condition_expr,
            report.play_count,
            report.comment_count,
            report.message_count,
        ):
            matched_rule = rule
            break

    if not matched_rule:
        diagnosis = DiagnosisResult(
            task_id=report.task_id,
            problem_type="normal",
            problem_desc="数据表现正常，继续保持",
            optimization_direction="继续当前策略",
            optimization_detail="内容表现良好，建议保持当前内容方向，可以尝试不同的情绪结构变体来测试效果",
        )
    else:
        diagnosis = DiagnosisResult(
            task_id=report.task_id,
            problem_type=matched_rule.problem_type,
            problem_desc=_generate_problem_desc(matched_rule.problem_type, report),
            optimization_direction=matched_rule.optimization_direction,
            optimization_detail=matched_rule.optimization_prompt,
        )

    db.add(diagnosis)
    await db.commit()
    await db.refresh(diagnosis)

    logger.info(
        f"Diagnosis completed for task {report.task_id}: "
        f"type={diagnosis.problem_type}, "
        f"play={report.play_count}, comment={report.comment_count}, msg={report.message_count}"
    )

    return diagnosis


def _generate_problem_desc(problem_type: str, report: PerformanceReport) -> str:
    if problem_type == "hook_weak":
        return f"播放量仅{report.play_count}，钩子吸引力极弱，需要彻底更换钩子策略"
    elif problem_type == "title_weak":
        return f"播放量{report.play_count}偏低，标题或选题吸引力不足"
    elif problem_type == "interaction_weak":
        return f"播放量{report.play_count}但评论仅{report.comment_count}条，互动引导偏弱"
    elif problem_type == "conversion_weak":
        return f"评论{report.comment_count}条但私信为0，转化话术需要优化"
    elif problem_type == "normal":
        return f"数据表现正常：播放{report.play_count}，评论{report.comment_count}，私信{report.message_count}"
    return "数据表现待分析"
