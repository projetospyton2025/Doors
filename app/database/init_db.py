from app.config import BASE_DIR, get_settings
from app.database import session as db_session
from app.models import Application, Language  # noqa: F401
from app.repositories.application_repository import ApplicationRepository
from app.repositories.language_repository import LanguageRepository
from app.schemas.application import ApplicationCreate
from app.services.application_service import ApplicationService
from app.services.import_service import ImportService
from app.utils.constants import LANGUAGE_CPP, LANGUAGE_HTML, LANGUAGE_PYTHON
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
        languages.ensure(LANGUAGE_CPP)
        db.commit()

        if settings.app_env != "test":
            seed = settings.seed_xlsx_path
            if seed.exists():
                ImportService(db).import_xlsx(seed)
            _ensure_self_application(db, settings.app_port)
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
