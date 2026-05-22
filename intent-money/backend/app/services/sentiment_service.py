import asyncio
import logging

from snownlp import SnowNLP

logger = logging.getLogger(__name__)


def _classify_label(score: float) -> str:
    if score >= 0.6:
        return "positive"
    elif score >= 0.4:
        return "neutral"
    return "negative"


def analyze_sentiment(text: str) -> dict:
    try:
        s = SnowNLP(text)
        score = float(s.sentiments)
        return {"score": score, "label": _classify_label(score)}
    except Exception as e:
        logger.error(f"SnowNLP analyze failed: {e}")
        return {"score": 0.5, "label": "neutral"}


async def analyze_sentiment_async(text: str) -> dict:
    return await asyncio.to_thread(analyze_sentiment, text)


def analyze_comments_batch(comments: list[str]) -> dict:
    details: list[dict] = []
    positive = 0
    neutral = 0
    negative = 0
    total_score = 0.0

    for text in comments:
        result = analyze_sentiment(text)
        details.append(result)
        total_score += result["score"]
        if result["label"] == "positive":
            positive += 1
        elif result["label"] == "neutral":
            neutral += 1
        else:
            negative += 1

    total = len(comments)
    avg_score = round(total_score / total, 4) if total > 0 else 0.0

    return {
        "total": total,
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "avg_score": avg_score,
        "details": details,
    }


async def analyze_comments_batch_async(comments: list[str]) -> dict:
    return await asyncio.to_thread(analyze_comments_batch, comments)
