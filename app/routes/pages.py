from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.utils.constants import PLANS

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"page": "dashboard", "plans": PLANS},
    )


@router.get("/applications", response_class=HTMLResponse)
def applications_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "applications.html",
        {"page": "applications", "plans": PLANS},
    )


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "settings.html",
        {"page": "settings", "plans": PLANS},
    )
