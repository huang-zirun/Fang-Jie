import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.database import async_session_factory, engine, Base
from app.seed import PLATFORM_ID_DOUYIN, PLATFORM_ID_XIAOHONGSHU, seed_all

logger = logging.getLogger(__name__)


async def daily_market_analysis():
    while True:
        await asyncio.sleep(86400)
        try:
            async with async_session_factory() as db:
                from app.services.market_service import analyze_market_trend
                for platform_id in [PLATFORM_ID_DOUYIN, PLATFORM_ID_XIAOHONGSHU]:
                    await analyze_market_trend(db, platform_id)
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")


async def weekly_evolution():
    while True:
        await asyncio.sleep(604800)
        try:
            async with async_session_factory() as db:
                from app.services.evolution_service import adjust_rule_weights
                result = await adjust_rule_weights(db)
                logger.info(f"Weekly evolution: {result}")
        except Exception as e:
            logger.error(f"Evolution failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_all()
    asyncio.create_task(daily_market_analysis())
    asyncio.create_task(weekly_evolution())
    yield


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
