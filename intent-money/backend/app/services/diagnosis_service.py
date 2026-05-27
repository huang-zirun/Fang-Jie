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
from app.models.performance_snapshot import PerformanceSnapshot
from app.utils.time import utc_now_naive

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


def _compute_trend(snapshots: list[PerformanceSnapshot], deployed_at=None) -> dict:
    if not snapshots:
        return {
            "snapshot_count": 0,
            "days_since_deploy": 0,
            "play_trend": "no_data",
            "avg_daily_play_growth": 0.0,
            "latest_play_count": 0,
            "latest_comment_count": 0,
            "latest_message_count": 0,
        }

    latest = snapshots[-1]
    snapshot_count = len(snapshots)

    days_since_deploy = 0
    if deployed_at:
        now = utc_now_naive()
        delta = now - deployed_at.replace(tzinfo=None) if deployed_at.tzinfo else now - deployed_at
        days_since_deploy = max(delta.days, 0)
    elif snapshots:
        first = snapshots[0]
        first_time = first.snapshot_at.replace(tzinfo=None) if first.snapshot_at and first.snapshot_at.tzinfo else first.snapshot_at
        now = utc_now_naive()
        if first_time:
            delta = now - first_time
            days_since_deploy = max(delta.days, 1)

    avg_daily_play_growth = 0.0
    play_trend = "steady"

    if days_since_deploy > 0:
        first = snapshots[0]
        play_diff = latest.play_count - first.play_count
        avg_daily_play_growth = round(play_diff / days_since_deploy, 1)

        if avg_daily_play_growth <= 0:
            play_trend = "declining"
        elif avg_daily_play_growth < 100:
            play_trend = "slow_growth"
        elif avg_daily_play_growth < 1000:
            play_trend = "steady"
        else:
            play_trend = "viral"
    elif snapshot_count >= 2:
        first = snapshots[0]
        play_diff = latest.play_count - first.play_count
        if play_diff <= 0:
            play_trend = "declining"
        elif play_diff < 100:
            play_trend = "slow_growth"
        elif play_diff < 1000:
            play_trend = "steady"
        else:
            play_trend = "viral"

    return {
        "snapshot_count": snapshot_count,
        "days_since_deploy": days_since_deploy,
        "play_trend": play_trend,
        "avg_daily_play_growth": avg_daily_play_growth,
        "latest_play_count": latest.play_count,
        "latest_comment_count": latest.comment_count,
        "latest_message_count": latest.message_count,
    }


def _generate_problem_desc_from_snapshot(problem_type: str, latest: PerformanceSnapshot, trend: dict) -> str:
    play = latest.play_count
    comment = latest.comment_count
    message = latest.message_count
    days = trend["days_since_deploy"]
    trend_label = trend["play_trend"]

    base_descs = {
        "hook_weak": f"投放{days}天播放量仅{play}（趋势：{trend_label}），钩子吸引力极弱，需要彻底更换钩子策略",
        "title_weak": f"投放{days}天播放量{play}偏低（趋势：{trend_label}），标题或选题吸引力不足",
        "interaction_weak": f"播放量{play}但评论仅{comment}条，互动引导偏弱",
        "conversion_weak": f"评论{comment}条但私信为0，转化话术需要优化",
        "sale_weak": f"播放量{play}但私信为0，成交话术弱，需要优化促单话术",
        "price_sensitive": f"评论{comment}条但私信为0，价格敏感度高，需要增加价值感话术",
        "trust_weak": f"投放{days}天播放量仅{play}（趋势：{trend_label}），信任感不足，需要增加背书和真实体验",
        "recruit_weak": f"投放{days}天播放量仅{play}（趋势：{trend_label}），招募吸引力弱，需要突出收益和低门槛",
        "barrier_high": f"播放量{play}但评论仅{comment}条，入门门槛感知高，需要简化流程描述",
        "retention_weak": f"评论{comment}条但私信为0，留存转化弱，需要增加团队支持话术",
        "identity_weak": f"投放{days}天播放量仅{play}（趋势：{trend_label}），人设辨识度低，需要强化个人标签",
        "content_weak": f"播放量{play}但评论仅{comment}条，内容互动弱，需要增加话题讨论引导",
        "growth_slow": f"评论{comment}条但私信仅{message}条，粉丝转化慢，需要增加关注引导",
        "normal": f"数据表现正常：播放{play}，评论{comment}，私信{message}，趋势{trend_label}",
    }
    return base_descs.get(problem_type, "数据表现待分析")


async def _ai_deep_analysis_from_snapshots(
    task: ContentTask,
    snapshots: list[PerformanceSnapshot],
    trend: dict,
    problem_type: str,
    problem_desc: str,
) -> dict | None:
    if not settings.AI_API_KEY:
        return None

    latest = snapshots[-1]
    snapshot_lines = []
    for s in snapshots:
        snapshot_lines.append(f"  - {s.snapshot_at.isoformat() if s.snapshot_at else 'N/A'}: 播放{s.play_count}, 评论{s.comment_count}, 私信{s.message_count} (来源: {s.source})")

    prompt = (
        "你是一名内容运营诊断专家。\n"
        "\n"
        "## 任务\n"
        "基于以下内容数据和时间序列表现数据，深度分析内容问题并给出优化建议。\n"
        "\n"
        "## 内容数据\n"
        f"- 钩子: {task.hook_text}\n"
        f"- 口播: {task.script_text}\n"
        f"- 标题: {task.title}\n"
        f"- 评论区话术: {task.comment_template}\n"
        "\n"
        "## 表现数据（时间序列）\n"
        f"- 快照数量: {trend['snapshot_count']}\n"
        f"- 投放天数: {trend['days_since_deploy']}\n"
        f"- 播放趋势: {trend['play_trend']}\n"
        f"- 日均播放增长: {trend['avg_daily_play_growth']}\n"
        "\n"
        "## 快照明细\n"
        + "\n".join(snapshot_lines) + "\n"
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


async def diagnose_from_snapshots(
    db: AsyncSession,
    task: ContentTask,
    snapshots: list[PerformanceSnapshot],
) -> DiagnosisResult:
    trend = _compute_trend(snapshots, task.deployed_at)
    latest = snapshots[-1]

    intent_id = task.intent_id

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
            latest.play_count,
            latest.comment_count,
            latest.message_count,
        ):
            matched_rule = rule
            break

    if not matched_rule:
        diagnosis = DiagnosisResult(
            task_id=task.id,
            problem_type="normal",
            problem_desc=_generate_problem_desc_from_snapshot("normal", latest, trend),
            optimization_direction="继续当前策略",
            optimization_detail="内容表现良好，建议保持当前内容方向，可以尝试不同的情绪结构变体来测试效果",
            snapshot_count=trend["snapshot_count"],
            days_since_deploy=trend["days_since_deploy"],
            play_trend=trend["play_trend"],
            avg_daily_play_growth=trend["avg_daily_play_growth"],
        )
    else:
        diagnosis = DiagnosisResult(
            task_id=task.id,
            problem_type=matched_rule.problem_type,
            problem_desc=_generate_problem_desc_from_snapshot(matched_rule.problem_type, latest, trend),
            optimization_direction=matched_rule.optimization_direction,
            optimization_detail=matched_rule.optimization_prompt,
            snapshot_count=trend["snapshot_count"],
            days_since_deploy=trend["days_since_deploy"],
            play_trend=trend["play_trend"],
            avg_daily_play_growth=trend["avg_daily_play_growth"],
        )

    ai_analysis = None
    rule_confidence = None

    if diagnosis.problem_type != "normal":
        ai_result = await _ai_deep_analysis_from_snapshots(
            task, snapshots, trend, diagnosis.problem_type, diagnosis.problem_desc
        )
        if ai_result:
            ai_analysis = json.dumps(ai_result, ensure_ascii=False)
            rule_confidence = ai_result.get("confidence", 0.5)
        else:
            rule_confidence = 0.5

    diagnosis.ai_analysis = ai_analysis
    diagnosis.rule_confidence = rule_confidence

    sentiment_signal = None
    if task.platform_id and settings.SENTIMENT_ENABLED:
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
        f"Snapshot diagnosis completed for task {task.id}: "
        f"type={diagnosis.problem_type}, "
        f"play={latest.play_count}, comment={latest.comment_count}, msg={latest.message_count}, "
        f"snapshots={trend['snapshot_count']}, days={trend['days_since_deploy']}, "
        f"trend={trend['play_trend']}, avg_growth={trend['avg_daily_play_growth']}, "
        f"ai={'yes' if ai_analysis else 'no'}, confidence={rule_confidence}"
    )

    return diagnosis
