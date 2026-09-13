from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.utils.constants import PLANS
from app.utils.prefix import resolve_prefix

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
router = APIRouter()


def _page_context(request: Request, **extra) -> dict:
    return {"app_root": resolve_prefix(request), **extra}


@router.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def dashboard_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        _page_context(request, page="dashboard", plans=PLANS),
    )


@router.api_route("/applications", methods=["GET", "HEAD"], response_class=HTMLResponse)
def applications_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "applications.html",
        _page_context(request, page="applications", plans=PLANS),
    )


@router.api_route("/settings", methods=["GET", "HEAD"], response_class=HTMLResponse)
def settings_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "settings.html",
        _page_context(request, page="settings", plans=PLANS),
    )
