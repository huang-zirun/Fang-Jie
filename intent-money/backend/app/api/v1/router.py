from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.conversion_paths import router as conversion_paths_router
from app.api.v1.content_structures import router as content_structures_router
from app.api.v1.events import router as events_router
from app.api.v1.intents import router as intents_router
from app.api.v1.intents import platforms_router
from app.api.v1.market import router as market_router
from app.api.v1.publisher import router as publisher_router
from app.api.v1.scraper import router as scraper_router
from app.api.v1.structure_extractor import router as structure_extractor_router
from app.api.v1.tasks import router as tasks_router

router = APIRouter()
router.include_router(admin_router)
router.include_router(auth_router)
router.include_router(conversion_paths_router)
router.include_router(content_structures_router)
router.include_router(events_router)
router.include_router(intents_router)
router.include_router(platforms_router)
router.include_router(market_router)
router.include_router(publisher_router)
router.include_router(scraper_router)
router.include_router(structure_extractor_router)
router.include_router(tasks_router)
