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
from app.services.platform_scraper import douyin_scraper
from app.services.platform_scraper.cdp_douyin_scraper import CdpDouyinScraper
from app.services.platform_scraper.cdp_xhs_scraper import CdpXhsScraper
from app.services.platform_scraper.xhs_scraper import XhsScraper
from app.services.sentiment_service import analyze_comments_batch_async

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


async def scrape_and_save_xhs_notes(db: AsyncSession, keyword: str) -> int:
    try:
        scraper = CdpXhsScraper() if settings.CDP_ENABLED else XhsScraper()
        notes = await scraper.search_hot_notes(keyword=keyword)
    except Exception as e:
        logger.error(f"XHS scrape failed for keyword '{keyword}': {e}")
        return 0

    if not notes:
        logger.info(f"XHS scrape returned no results for keyword '{keyword}'")
        return 0

    platform_result = await db.execute(
        select(Platform).where(Platform.name == "小红书")
    )
    platform = platform_result.scalars().first()
    if not platform:
        logger.warning("Platform '小红书' not found, skipping save")
        return 0

    saved_count = 0
    for note in notes:
        try:
            analysis_result = {
                "note_id": note.get("note_id", ""),
                "title": note.get("title", ""),
                "author": note.get("author", ""),
                "liked_count": note.get("liked_count", "0"),
                "collected_count": note.get("collected_count", "0"),
                "comment_count": note.get("comment_count", "0"),
                "share_count": note.get("share_count", "0"),
                "note_type": note.get("note_type", ""),
                "tag_list": note.get("tag_list", []),
            }

            comment_sentiment = None
            if settings.SENTIMENT_ENABLED:
                try:
                    note_id = note.get("note_id", "")
                    if note_id:
                        comments = await scraper.get_note_comments(note_id, limit=50)
                        comment_texts = [c.get("content", "") for c in comments if c.get("content")]
                        if comment_texts:
                            sentiment_result = await analyze_comments_batch_async(comment_texts)
                            comment_sentiment = {
                                "total": sentiment_result["total"],
                                "positive": sentiment_result["positive"],
                                "neutral": sentiment_result["neutral"],
                                "negative": sentiment_result["negative"],
                                "avg_score": sentiment_result["avg_score"],
                            }
                except Exception as e:
                    logger.error(f"XHS comment sentiment analysis failed for note: {e}")

            hot = MarketHot(
                platform_id=platform.id,
                keyword=keyword,
                hot_type="xhs_note",
                analysis_result=analysis_result,
                recommended_structures=note.get("tag_list", []),
                priority_boost=float(note.get("liked_count", "0") or 0),
                comment_sentiment=comment_sentiment,
                is_active=True,
            )
            db.add(hot)
            saved_count += 1
        except Exception as e:
            logger.error(f"Failed to save XHS note: {e}")
            continue

    try:
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to commit XHS notes: {e}")
        await db.rollback()
        return 0

    return saved_count


async def scrape_and_save_hot_videos(db: AsyncSession, platform_id: uuid.UUID, keyword: str) -> int:
    if not settings.SCRAPER_ENABLED:
        logger.info("Scraper is disabled, skipping scrape_and_save_hot_videos")
        return 0

    try:
        scraper = CdpDouyinScraper() if settings.CDP_ENABLED else douyin_scraper
        videos = await scraper.search_hot_videos(keyword, limit=20)
    except Exception as e:
        logger.error(f"Scrape hot videos failed for keyword '{keyword}': {e}")
        return 0

    if not videos:
        logger.info(f"No videos found for keyword '{keyword}'")
        return 0

    saved_count = 0
    for video in videos:
        try:
            stats = video.get("statistics", {})
            play_count = stats.get("play_count", 0)
            digg_count = stats.get("digg_count", 0)
            comment_count = stats.get("comment_count", 0)
            share_count = stats.get("share_count", 0)

            total_engagement = digg_count + comment_count + share_count
            priority_boost = min(total_engagement / 10000.0, 100.0) if play_count > 0 else 0.0

            tags = video.get("tags", [])

            comment_sentiment = None
            if settings.SENTIMENT_ENABLED:
                try:
                    video_id = video.get("video_id", "")
                    if video_id:
                        comments = await scraper.get_video_comments(video_id, limit=50)
                        comment_texts = [c.get("content", "") for c in comments if c.get("content")]
                        if comment_texts:
                            sentiment_result = await analyze_comments_batch_async(comment_texts)
                            comment_sentiment = {
                                "total": sentiment_result["total"],
                                "positive": sentiment_result["positive"],
                                "neutral": sentiment_result["neutral"],
                                "negative": sentiment_result["negative"],
                                "avg_score": sentiment_result["avg_score"],
                            }
                except Exception as e:
                    logger.error(f"Douyin comment sentiment analysis failed for video: {e}")

            hot = MarketHot(
                platform_id=platform_id,
                keyword=keyword,
                hot_type="trending_video",
                analysis_result={
                    "video_id": video.get("video_id", ""),
                    "title": video.get("title", ""),
                    "author": video.get("author", {}),
                    "statistics": stats,
                    "tags": tags,
                    "created_at": video.get("created_at"),
                    "share_url": video.get("share_url", ""),
                },
                recommended_structures=tags if tags else None,
                priority_boost=priority_boost,
                comment_sentiment=comment_sentiment,
                is_active=True,
            )
            db.add(hot)
            saved_count += 1
        except Exception as e:
            logger.error(f"Failed to save video hot record: {e}")
            continue

    try:
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to commit scraped hot videos: {e}")
        await db.rollback()
        return 0

    logger.info(f"Saved {saved_count} hot videos for keyword '{keyword}'")
    return saved_count
