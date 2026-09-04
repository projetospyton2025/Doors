from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.application_service import ApplicationService
from app.services.export_service import ExportService


def get_application_service(db: Session = Depends(get_db)) -> ApplicationService:
    return ApplicationService(db)


def get_export_service() -> ExportService:
    return ExportService()
