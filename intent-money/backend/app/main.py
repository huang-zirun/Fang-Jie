import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 抑制第三方库的冗长英文日志
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

from app.api.v1.router import router as v1_router
from app.database import async_session_factory, engine, Base
from app.models import ExtractedStructure  # noqa: F401
from app.models.user_event import UserEvent  # noqa: F401
from app.seed import PLATFORM_ID_DOUYIN, PLATFORM_ID_XIAOHONGSHU, seed_all

logger = logging.getLogger(__name__)

_background_tasks: list[asyncio.Task] = []


async def daily_market_analysis():
    while True:
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            logger.info("每日市场分析已取消")
            return
        try:
            async with async_session_factory() as db:
                from app.services.market_service import analyze_market_trend
                for platform_id in [PLATFORM_ID_DOUYIN, PLATFORM_ID_XIAOHONGSHU]:
                    await analyze_market_trend(db, platform_id)
        except asyncio.CancelledError:
            logger.info("每日市场分析已取消")
            return
        except Exception as e:
            logger.error(f"市场分析失败: {e}")


async def daily_scrape_hot_videos():
    while True:
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            logger.info("每日热门抓取已取消")
            return
        try:
            async with async_session_factory() as db:
                from app.services.market_service import scrape_and_save_hot_videos, scrape_via_extension
                keywords = ["袜子", "好物推荐", "穿搭", "生活好物"]

                # 优先尝试扩展抓取路径（需要前端配合）
                ext_result = await scrape_via_extension(db, PLATFORM_ID_DOUYIN, keywords)
                logger.info(f"扩展抓取: {ext_result['message']}")

                # 同时尝试后端 API 爬虫作为降级
                for keyword in keywords:
                    saved = await scrape_and_save_hot_videos(db, PLATFORM_ID_DOUYIN, keyword)
                    if saved > 0:
                        logger.info(f"后端爬虫保存{saved}条'{keyword}'视频")
                    else:
                        logger.warning(f"后端爬虫未获取到'{keyword}'视频")
        except asyncio.CancelledError:
            logger.info("每日热门抓取已取消")
            return
        except Exception as e:
            logger.error(f"每日热门抓取失败: {e}")


async def extension_scrape_reminder():
    """定期提醒扩展抓取路径可用"""
    while True:
        try:
            await asyncio.sleep(21600)  # 6 hours
        except asyncio.CancelledError:
            logger.info("扩展抓取提醒已取消")
            return
        try:
            async with async_session_factory() as db:
                from sqlalchemy import func, select
                from app.models.market_hot import MarketHot
                # 检查是否有扩展提交的数据
                ext_count = await db.execute(
                    select(func.count()).select_from(MarketHot).where(
                        MarketHot.hot_type == "extension_scraped",
                        MarketHot.is_active.is_(True),
                    )
                )
                count = ext_count.scalar() or 0
                if count == 0:
                    logger.info("无扩展抓取数据，可通过浏览器扩展触发")
                else:
                    logger.info(f"发现{count}条扩展抓取数据")
        except asyncio.CancelledError:
            logger.info("扩展抓取提醒已取消")
            return
        except Exception as e:
            logger.error(f"扩展抓取提醒失败: {e}")


async def weekly_evolution():
    while True:
        try:
            await asyncio.sleep(604800)
        except asyncio.CancelledError:
            logger.info("每周进化已取消")
            return
        try:
            async with async_session_factory() as db:
                from app.services.evolution_service import adjust_rule_weights
                result = await adjust_rule_weights(db)
                logger.info(f"每周进化: {result}")
        except asyncio.CancelledError:
            logger.info("每周进化已取消")
            return
        except Exception as e:
            logger.error(f"进化失败: {e}")


async def periodic_snapshot_fetch():
    while True:
        try:
            await asyncio.sleep(7200)
        except asyncio.CancelledError:
            logger.info("定期快照已取消")
            return
        try:
            from app.services.snapshot_scheduler import scheduled_snapshot_fetch
            await scheduled_snapshot_fetch()
        except asyncio.CancelledError:
            logger.info("定期快照已取消")
            return
        except Exception as e:
            logger.error(f"定期快照失败: {e}")


async def daily_cookie_validation():
    while True:
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            logger.info("每日Cookie校验已取消")
            return
        try:
            async with async_session_factory() as db:
                from app.services.cookie_lifecycle import validate_all_cookies
                count = await validate_all_cookies(db)
                logger.info(f"每日Cookie校验: 检查{count}个Cookie")
        except asyncio.CancelledError:
            logger.info("每日Cookie校验已取消")
            return
        except Exception as e:
            logger.error(f"每日Cookie校验失败: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 生产环境使用 alembic 迁移管理表结构，跳过 create_all
    # 开发环境仍然使用 create_all 确保表存在
    if settings.ENV != "production":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    await seed_all()

    _background_tasks.append(asyncio.create_task(daily_market_analysis()))
    _background_tasks.append(asyncio.create_task(daily_scrape_hot_videos()))
    _background_tasks.append(asyncio.create_task(weekly_evolution()))
    _background_tasks.append(asyncio.create_task(periodic_snapshot_fetch()))
    _background_tasks.append(asyncio.create_task(daily_cookie_validation()))
    _background_tasks.append(asyncio.create_task(extension_scrape_reminder()))

    logger.info("后台任务已全部启动")

    yield

    for task in _background_tasks:
        task.cancel()
    results = await asyncio.gather(*_background_tasks, return_exceptions=True)
    for task, result in zip(_background_tasks, results):
        if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
            logger.error(f"后台任务异常退出: {result}")
    _background_tasks.clear()
    logger.info("后台任务已全部取消")


app = FastAPI(title="Intent Money OS", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
