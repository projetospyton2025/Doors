from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.language import Language


class LanguageRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Language]:
        return list(self.db.scalars(select(Language).order_by(Language.name.asc())).all())

    def get_by_name(self, name: str) -> Language | None:
        return self.db.scalar(select(Language).where(Language.name == name))

    def create(self, name: str) -> Language:
        language = Language(name=name)
        self.db.add(language)
        self.db.flush()
        return language

    def ensure(self, name: str) -> Language:
        existing = self.get_by_name(name)
        if existing:
            return existing
        return self.create(name)
