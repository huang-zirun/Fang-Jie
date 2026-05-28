import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
            logger.info("daily_market_analysis cancelled, exiting")
            return
        try:
            async with async_session_factory() as db:
                from app.services.market_service import analyze_market_trend
                for platform_id in [PLATFORM_ID_DOUYIN, PLATFORM_ID_XIAOHONGSHU]:
                    await analyze_market_trend(db, platform_id)
        except asyncio.CancelledError:
            logger.info("daily_market_analysis cancelled during work, exiting")
            return
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")


async def daily_scrape_hot_videos():
    while True:
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            logger.info("daily_scrape_hot_videos cancelled, exiting")
            return
        try:
            async with async_session_factory() as db:
                from app.services.market_service import scrape_and_save_hot_videos
                keywords = ["袜子", "好物推荐", "穿搭", "生活好物"]
                for keyword in keywords:
                    await scrape_and_save_hot_videos(db, PLATFORM_ID_DOUYIN, keyword)
        except asyncio.CancelledError:
            logger.info("daily_scrape_hot_videos cancelled during work, exiting")
            return
        except Exception as e:
            logger.error(f"Daily scrape hot videos failed: {e}")


async def weekly_evolution():
    while True:
        try:
            await asyncio.sleep(604800)
        except asyncio.CancelledError:
            logger.info("weekly_evolution cancelled, exiting")
            return
        try:
            async with async_session_factory() as db:
                from app.services.evolution_service import adjust_rule_weights
                result = await adjust_rule_weights(db)
                logger.info(f"Weekly evolution: {result}")
        except asyncio.CancelledError:
            logger.info("weekly_evolution cancelled during work, exiting")
            return
        except Exception as e:
            logger.error(f"Evolution failed: {e}")


async def periodic_snapshot_fetch():
    while True:
        try:
            await asyncio.sleep(7200)
        except asyncio.CancelledError:
            logger.info("periodic_snapshot_fetch cancelled, exiting")
            return
        try:
            from app.services.snapshot_scheduler import scheduled_snapshot_fetch
            await scheduled_snapshot_fetch()
        except asyncio.CancelledError:
            logger.info("periodic_snapshot_fetch cancelled during work, exiting")
            return
        except Exception as e:
            logger.error(f"Periodic snapshot fetch failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_all()

    _background_tasks.append(asyncio.create_task(daily_market_analysis()))
    _background_tasks.append(asyncio.create_task(daily_scrape_hot_videos()))
    _background_tasks.append(asyncio.create_task(weekly_evolution()))
    _background_tasks.append(asyncio.create_task(periodic_snapshot_fetch()))

    logger.info("All background tasks started")

    yield

    for task in _background_tasks:
        task.cancel()
    results = await asyncio.gather(*_background_tasks, return_exceptions=True)
    for task, result in zip(_background_tasks, results):
        if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
            logger.error(f"Background task exited with error: {result}")
    _background_tasks.clear()
    logger.info("All background tasks cancelled")


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
