from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app import __version__
from app.config import BASE_DIR, get_settings
from app.database.init_db import init_db
from app.database.session import init_engine
from app.routes import router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    get_settings().data_dir
    get_settings().exports_dir
    init_engine()
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description="Gestão de aplicações, portas e infraestrutura.",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url=None,
    )

    if settings.host_list and settings.host_list != ["*"]:
        application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.host_list)

    application.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
    application.include_router(router)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.exception_handler(StarletteHTTPException)
    async def safe_http_exception(request: Request, exc: StarletteHTTPException):
        if settings.debug:
            return await http_exception_handler(request, exc)
        detail = exc.detail
        if isinstance(detail, dict):
            return JSONResponse(status_code=exc.status_code, content={"detail": detail})
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": {"message": "Não foi possível concluir a operação."}},
        )

    return application


app = create_app()
