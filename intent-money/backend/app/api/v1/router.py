from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.content_structures import router as content_structures_router
from app.api.v1.intents import router as intents_router
from app.api.v1.tasks import router as tasks_router

router = APIRouter()
router.include_router(admin_router)
router.include_router(auth_router)
router.include_router(content_structures_router)
router.include_router(intents_router)
router.include_router(tasks_router)
