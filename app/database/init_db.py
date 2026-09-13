from sqlalchemy import func, select

from app.config import BASE_DIR, get_settings
from app.database import session as db_session
from app.models import Application, Language  # noqa: F401
from app.repositories.application_repository import ApplicationRepository
from app.repositories.language_repository import LanguageRepository
from app.schemas.application import ApplicationCreate
from app.services.application_service import ApplicationService
from app.services.import_service import ImportService
from app.utils.constants import LANGUAGE_HTML, LANGUAGE_PYTHON, WORK_LINKS_SEED
from app.utils.validators import ValidationError


def init_db() -> None:
    engine = db_session.get_engine()
    db_session.Base.metadata.create_all(bind=engine)
    settings = get_settings()
    if db_session.SessionLocal is None:
        db_session.init_engine()
    assert db_session.SessionLocal is not None
    db = db_session.SessionLocal()
    try:
        languages = LanguageRepository(db)
        languages.ensure(LANGUAGE_PYTHON)
        languages.ensure(LANGUAGE_HTML)
        db.commit()

        has_records = (db.scalar(select(func.count(Application.id))) or 0) > 0
        xlsx = settings.xlsx_path
        if not has_records and xlsx.exists():
            ImportService(db).import_xlsx(xlsx)
            db.commit()
        if settings.app_env != "test":
            _ensure_self_application(db, settings.app_port)
            _ensure_work_links(db)
    finally:
        db.close()


def _ensure_self_application(db, door: int) -> None:
    if ApplicationRepository(db).get_by_door(door):
        return
    try:
        ApplicationService(db).create(
            ApplicationCreate(
                app_name="Doors",
                path=str(BASE_DIR),
                door=door,
                language=LANGUAGE_PYTHON,
                nginx=None,
                docker="Sim",
                plan="work",
                github=None,
                drive=None,
            )
        )
    except (ValidationError, LookupError):
        db.rollback()


def _ensure_work_links(db) -> None:
    """Garante os 4 sistemas Work do links.xlsx (coluna Remoto) sem duplicar porta/nome."""
    repo = ApplicationRepository(db)
    service = ApplicationService(db)
    for item in WORK_LINKS_SEED:
        if repo.get_by_door(item["door"]):
            existing = repo.get_by_door(item["door"])
            # Atualiza só o link Remoto se a porta já existir sem URL
            if existing and not existing.nginx and item.get("nginx"):
                existing.nginx = item["nginx"]
                db.commit()
            continue
        try:
            service.create(
                ApplicationCreate(
                    app_name=item["app_name"],
                    path=item["path"],
                    door=item["door"],
                    language=LANGUAGE_PYTHON,
                    nginx=item.get("nginx"),
                    docker="Não",
                    plan="work",
                    github=None,
                    drive=None,
                )
            )
        except (ValidationError, LookupError):
            db.rollback()
