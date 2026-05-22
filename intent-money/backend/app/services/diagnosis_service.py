import json
import logging

from openai import APIError, APITimeoutError, AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.content_task import ContentTask
from app.models.diagnosis_result import DiagnosisResult
from app.models.market_hot import MarketHot
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


async def _ai_deep_analysis(
    task: ContentTask,
    report: PerformanceReport,
    problem_type: str,
    problem_desc: str,
) -> dict | None:
    if not settings.AI_API_KEY:
        return None

    prompt = (
        "你是一名内容运营诊断专家。\n"
        "\n"
        "## 任务\n"
        "基于以下内容数据和表现数据，深度分析内容问题并给出优化建议。\n"
        "\n"
        "## 内容数据\n"
        f"- 钩子: {task.hook_text}\n"
        f"- 口播: {task.script_text}\n"
        f"- 标题: {task.title}\n"
        f"- 评论区话术: {task.comment_template}\n"
        "\n"
        "## 表现数据\n"
        f"- 播放量: {report.play_count}\n"
        f"- 评论数: {report.comment_count}\n"
        f"- 私信数: {report.message_count}\n"
        "\n"
        "## 初步规则诊断\n"
        f"- 问题类型: {problem_type}\n"
        f"- 问题描述: {problem_desc}\n"
        "\n"
        "## 输出格式（严格 JSON）\n"
        "{\n"
        '    "root_cause": "问题根因分析",\n'
        '    "specific_suggestions": ["具体建议1", "具体建议2", "具体建议3"],\n'
        '    "confidence": 0.85\n'
        "}"
    )

    client = AsyncOpenAI(
        api_key=settings.AI_API_KEY,
        base_url=settings.AI_BASE_URL,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
            timeout=10.0,
        )

        text = response.choices[0].message.content or ""

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        data = json.loads(text.strip())

        if not isinstance(data, dict) or "root_cause" not in data:
            logger.warning("AI analysis output missing required fields")
            return None

        return data

    except APITimeoutError:
        logger.warning("AI diagnosis timeout")
    except APIError as e:
        logger.error(f"AI diagnosis API error: {e}")
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning(f"AI diagnosis parse error: {e}")

    return None


async def diagnose_performance(
    db: AsyncSession,
    report: PerformanceReport,
) -> DiagnosisResult:
    task_result = await db.execute(
        select(ContentTask).where(ContentTask.id == report.task_id)
    )
    task = task_result.scalars().first()
    intent_id = task.intent_id if task else None

    query = (
        select(OptimizationRule)
        .where(OptimizationRule.is_active.is_(True))
        .order_by(OptimizationRule.priority.desc())
    )
    result = await db.execute(query)
    rules = result.scalars().all()

    intent_rules = [r for r in rules if r.intent_id is not None and r.intent_id == intent_id]
    global_rules = [r for r in rules if r.intent_id is None]

    matched_rule = None
    for rule in intent_rules + global_rules:
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

    ai_analysis = None
    rule_confidence = None

    if task and diagnosis.problem_type != "normal":
        ai_result = await _ai_deep_analysis(
            task, report, diagnosis.problem_type, diagnosis.problem_desc
        )
        if ai_result:
            ai_analysis = json.dumps(ai_result, ensure_ascii=False)
            rule_confidence = ai_result.get("confidence", 0.5)
        else:
            rule_confidence = 0.5

    diagnosis.ai_analysis = ai_analysis
    diagnosis.rule_confidence = rule_confidence

    sentiment_signal = None
    if task and task.platform_id and settings.SENTIMENT_ENABLED:
        try:
            hot_result = await db.execute(
                select(MarketHot).where(
                    MarketHot.platform_id == task.platform_id,
                    MarketHot.is_active.is_(True),
                    MarketHot.comment_sentiment.isnot(None),
                )
            )
            hots_with_sentiment = hot_result.scalars().all()

            if hots_with_sentiment:
                total_positive = sum(h.comment_sentiment.get("positive", 0) for h in hots_with_sentiment if h.comment_sentiment)
                total_neutral = sum(h.comment_sentiment.get("neutral", 0) for h in hots_with_sentiment if h.comment_sentiment)
                total_negative = sum(h.comment_sentiment.get("negative", 0) for h in hots_with_sentiment if h.comment_sentiment)
                total_all = total_positive + total_neutral + total_negative

                if total_all > 0:
                    positive_ratio = total_positive / total_all
                    negative_ratio = total_negative / total_all

                    if positive_ratio > 0.6:
                        sentiment_signal = "effective"
                    elif negative_ratio > 0.4:
                        sentiment_signal = "needs_optimization"
                    else:
                        sentiment_signal = "neutral"
        except Exception as e:
            logger.error(f"Sentiment signal analysis failed: {e}")

    additional_data = {}
    if sentiment_signal:
        additional_data["sentiment_signal"] = sentiment_signal
    if ai_analysis:
        try:
            ai_data = json.loads(ai_analysis)
            if isinstance(ai_data, dict):
                additional_data.update(ai_data)
        except (json.JSONDecodeError, TypeError):
            pass
    if additional_data:
        diagnosis.ai_analysis = json.dumps(additional_data, ensure_ascii=False)

    db.add(diagnosis)
    await db.commit()
    await db.refresh(diagnosis)

    logger.info(
        f"Diagnosis completed for task {report.task_id}: "
        f"type={diagnosis.problem_type}, "
        f"play={report.play_count}, comment={report.comment_count}, msg={report.message_count}, "
        f"ai={'yes' if ai_analysis else 'no'}, confidence={rule_confidence}"
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
    elif problem_type == "sale_weak":
        return f"播放量{report.play_count}但私信为0，成交话术弱，需要优化促单话术"
    elif problem_type == "price_sensitive":
        return f"评论{report.comment_count}条但私信为0，价格敏感度高，需要增加价值感话术"
    elif problem_type == "trust_weak":
        return f"播放量仅{report.play_count}，信任感不足，需要增加背书和真实体验"
    elif problem_type == "recruit_weak":
        return f"播放量仅{report.play_count}，招募吸引力弱，需要突出收益和低门槛"
    elif problem_type == "barrier_high":
        return f"播放量{report.play_count}但评论仅{report.comment_count}条，入门门槛感知高，需要简化流程描述"
    elif problem_type == "retention_weak":
        return f"评论{report.comment_count}条但私信为0，留存转化弱，需要增加团队支持话术"
    elif problem_type == "identity_weak":
        return f"播放量仅{report.play_count}，人设辨识度低，需要强化个人标签"
    elif problem_type == "content_weak":
        return f"播放量{report.play_count}但评论仅{report.comment_count}条，内容互动弱，需要增加话题讨论引导"
    elif problem_type == "growth_slow":
        return f"评论{report.comment_count}条但私信仅{report.message_count}条，粉丝转化慢，需要增加关注引导"
    elif problem_type == "normal":
        return f"数据表现正常：播放{report.play_count}，评论{report.comment_count}，私信{report.message_count}"
    return "数据表现待分析"
