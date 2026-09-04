from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from app.schemas.application import (
    ApplicationCreate,
    ApplicationFilters,
    ApplicationOut,
    ApplicationUpdate,
    DashboardStats,
    LanguageCreate,
    LanguageOut,
    MessageOut,
    PaginatedApplications,
)
from app.services.application_service import ApplicationService
from app.services.export_service import ExportService
from app.services.import_service import ImportService
from app.utils.validators import ValidationError
from app.routes.deps import get_application_service, get_export_service
from app.database.session import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api")


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=422, detail={"field": exc.field, "message": exc.message})
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail={"message": str(exc)})
    return HTTPException(status_code=400, detail={"message": "Não foi possível processar a solicitação."})


def _filters(
    q: str | None = Query(default=None),
    plan: str | None = Query(default=None),
    language: str | None = Query(default=None),
    docker: str | None = Query(default=None),
    nginx: str | None = Query(default=None),
    sort: str = Query(default="app_name"),
    order: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> ApplicationFilters:
    return ApplicationFilters(
        q=q,
        plan=plan,
        language=language,
        docker=docker,
        nginx=nginx,
        sort=sort,
        order=order if order in {"asc", "desc"} else "asc",
        page=page,
        page_size=page_size,
    )


@router.get("/applications", response_model=PaginatedApplications)
def list_applications(
    filters: ApplicationFilters = Depends(_filters),
    service: ApplicationService = Depends(get_application_service),
) -> PaginatedApplications:
    try:
        return service.list_applications(filters)
    except ValidationError as exc:
        raise _http_error(exc) from exc


@router.post("/applications", response_model=ApplicationOut, status_code=201)
def create_application(
    payload: ApplicationCreate,
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationOut:
    try:
        return service.create(payload)
    except (ValidationError, LookupError) as exc:
        raise _http_error(exc) from exc


@router.get("/applications/{application_id}", response_model=ApplicationOut)
def get_application(
    application_id: int,
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationOut:
    try:
        return service.get(application_id)
    except LookupError as exc:
        raise _http_error(exc) from exc


@router.put("/applications/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationOut:
    try:
        return service.update(application_id, payload)
    except (ValidationError, LookupError) as exc:
        raise _http_error(exc) from exc


@router.delete("/applications/{application_id}", response_model=MessageOut)
def delete_application(
    application_id: int,
    service: ApplicationService = Depends(get_application_service),
) -> MessageOut:
    try:
        service.delete(application_id)
        return MessageOut(message="Aplicação excluída.")
    except LookupError as exc:
        raise _http_error(exc) from exc


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(service: ApplicationService = Depends(get_application_service)) -> DashboardStats:
    return service.dashboard()


@router.get("/languages", response_model=list[LanguageOut])
def list_languages(service: ApplicationService = Depends(get_application_service)) -> list[LanguageOut]:
    return service.list_languages()


@router.post("/languages", response_model=LanguageOut, status_code=201)
def create_language(
    payload: LanguageCreate,
    service: ApplicationService = Depends(get_application_service),
) -> LanguageOut:
    try:
        return service.create_language(payload)
    except ValidationError as exc:
        raise _http_error(exc) from exc


@router.get("/export/csv")
def export_csv(
    filters: ApplicationFilters = Depends(_filters),
    service: ApplicationService = Depends(get_application_service),
    exporter: ExportService = Depends(get_export_service),
) -> Response:
    items = service.list_for_export(filters)
    content = exporter.csv_bytes(items)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{exporter.filename("csv")}"'},
    )


@router.get("/export/xlsx")
def export_xlsx(
    filters: ApplicationFilters = Depends(_filters),
    service: ApplicationService = Depends(get_application_service),
    exporter: ExportService = Depends(get_export_service),
) -> Response:
    items = service.list_for_export(filters)
    content = exporter.xlsx_bytes(items, split_by_plan=not filters.plan)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{exporter.filename("xlsx")}"'},
    )


@router.post("/import/xlsx")
def import_xlsx(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    filename = (file.filename or "").lower()
    if not filename.endswith(".xlsx"):
        raise HTTPException(status_code=422, detail={"message": "Envie um arquivo .xlsx."})
    with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(file.file.read())
        tmp_path = Path(tmp.name)
    try:
        result = ImportService(db).import_xlsx(tmp_path)
        return result
    finally:
        tmp_path.unlink(missing_ok=True)
