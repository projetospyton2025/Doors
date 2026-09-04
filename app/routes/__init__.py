from fastapi import APIRouter

from app.routes.api import router as api_router
from app.routes.pages import router as pages_router

router = APIRouter()
router.include_router(pages_router)
router.include_router(api_router)
