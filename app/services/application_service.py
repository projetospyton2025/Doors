from datetime import datetime
from math import ceil

from sqlalchemy.orm import Session

from app.models.application import Application
from app.repositories.application_repository import ApplicationRepository
from app.repositories.language_repository import LanguageRepository
from app.schemas.application import (
    ApplicationCreate,
    ApplicationFilters,
    ApplicationOut,
    DashboardStats,
    LanguageCreate,
    LanguageOut,
    PaginatedApplications,
)
from app.utils.constants import LANGUAGE_CPP, LANGUAGE_HTML, LANGUAGE_PYTHON, PLAN_LABELS, Plan
from app.utils.validators import (
    ValidationError,
    docker_label,
    normalize_docker,
    normalize_door,
    normalize_language,
    normalize_optional_link,
    normalize_path,
    normalize_plan,
    normalize_required_name,
)


class ApplicationService:
    def __init__(self, db: Session):
        self.db = db
        self.applications = ApplicationRepository(db)
        self.languages = LanguageRepository(db)

    def to_out(self, item: Application) -> ApplicationOut:
        return ApplicationOut(
            id=item.id,
            app_name=item.app_name,
            path=item.path,
            door=item.door,
            language=item.language.name,
            nginx=item.nginx,
            docker=docker_label(item.uses_docker),
            uses_docker=item.uses_docker,
            uses_nginx=bool(item.nginx),
            plan=item.plan,
            plan_label=PLAN_LABELS.get(item.plan, item.plan),
            github=item.github,
            drive=item.drive,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _parse_docker_filter(self, value: str | None) -> bool | None:
        if value is None or value == "" or value.lower() == "all":
            return None
        return normalize_docker(value)

    def _parse_nginx_filter(self, value: str | None) -> bool | None:
        if value is None or value == "" or value.lower() == "all":
            return None
        lowered = value.lower()
        if lowered in {"sim", "yes", "true", "1"}:
            return True
        if lowered in {"não", "nao", "no", "false", "0"}:
            return False
        raise ValidationError("nginx", "Filtro de Nginx inválido.")

    def _validated_payload(self, payload: ApplicationCreate) -> dict:
        language_name = normalize_language(payload.language)
        language = self.languages.get_by_name(language_name)
        if language is None:
            raise ValidationError(
                "language",
                "Linguagem não cadastrada. Cadastre-a em Configurações antes de usar.",
            )
        return {
            "app_name": normalize_required_name(payload.app_name, "app_name", "O nome da aplicação"),
            "path": normalize_path(payload.path),
            "door": normalize_door(payload.door),
            "language": language,
            "nginx": normalize_optional_link(payload.nginx, "nginx"),
            "uses_docker": normalize_docker(payload.docker),
            "plan": normalize_plan(payload.plan),
            "github": normalize_optional_link(payload.github, "github"),
            "drive": normalize_optional_link(payload.drive, "drive"),
        }

    def list_applications(self, filters: ApplicationFilters) -> PaginatedApplications:
        plan = normalize_plan(filters.plan) if filters.plan else None
        language = normalize_language(filters.language) if filters.language else None
        uses_docker = self._parse_docker_filter(filters.docker)
        uses_nginx = self._parse_nginx_filter(filters.nginx)
        items, total = self.applications.list_filtered(
            q=filters.q,
            plan=plan,
            language=language,
            uses_docker=uses_docker,
            uses_nginx=uses_nginx,
            sort=filters.sort,
            order=filters.order,
            page=filters.page,
            page_size=filters.page_size,
        )
        pages = ceil(total / filters.page_size) if filters.page_size else 1
        return PaginatedApplications(
            items=[self.to_out(item) for item in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            pages=max(pages, 1 if total else 0),
        )

    def list_for_export(self, filters: ApplicationFilters) -> list[ApplicationOut]:
        plan = normalize_plan(filters.plan) if filters.plan else None
        language = normalize_language(filters.language) if filters.language else None
        items = self.applications.list_all_filtered(
            q=filters.q,
            plan=plan,
            language=language,
            uses_docker=self._parse_docker_filter(filters.docker),
            uses_nginx=self._parse_nginx_filter(filters.nginx),
            sort=filters.sort,
            order=filters.order,
        )
        return [self.to_out(item) for item in items]

    def get(self, application_id: int) -> ApplicationOut:
        item = self.applications.get(application_id)
        if item is None:
            raise LookupError("Aplicação não encontrada.")
        return self.to_out(item)

    def create(self, payload: ApplicationCreate) -> ApplicationOut:
        data = self._validated_payload(payload)
        if self.applications.get_by_door(data["door"]):
            raise ValidationError("door", "Já existe uma aplicação utilizando esta porta.")
        language = data.pop("language")
        item = Application(language_id=language.id, **data)
        created = self.applications.create(item)
        self.db.commit()
        self.db.refresh(created)
        return self.to_out(created)

    def update(self, application_id: int, payload: ApplicationCreate) -> ApplicationOut:
        item = self.applications.get(application_id)
        if item is None:
            raise LookupError("Aplicação não encontrada.")
        data = self._validated_payload(payload)
        existing = self.applications.get_by_door(data["door"], exclude_id=application_id)
        if existing:
            raise ValidationError("door", "Já existe uma aplicação utilizando esta porta.")
        language = data.pop("language")
        item.app_name = data["app_name"]
        item.path = data["path"]
        item.door = data["door"]
        item.language_id = language.id
        item.nginx = data["nginx"]
        item.uses_docker = data["uses_docker"]
        item.plan = data["plan"]
        item.github = data["github"]
        item.drive = data["drive"]
        item.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(item)
        return self.to_out(item)

    def delete(self, application_id: int) -> None:
        item = self.applications.get(application_id)
        if item is None:
            raise LookupError("Aplicação não encontrada.")
        self.applications.delete(item)
        self.db.commit()

    def delete_many(self, ids: list[int]) -> int:
        unique_ids = list(dict.fromkeys(item for item in ids if item > 0))
        if not unique_ids:
            raise ValidationError("ids", "Selecione ao menos uma aplicação.")
        deleted = self.applications.delete_by_ids(unique_ids)
        if deleted == 0:
            raise LookupError("Nenhuma aplicação encontrada.")
        self.db.commit()
        return deleted

    def dashboard(self) -> DashboardStats:
        return DashboardStats(
            total=self.applications.count_all(),
            work=self.applications.count_by_plan(Plan.WORK.value),
            personal=self.applications.count_by_plan(Plan.PERSONAL.value),
            lotteries=self.applications.count_by_plan(Plan.LOTTERIES.value),
            python=self.applications.count_by_language(LANGUAGE_PYTHON),
            html=self.applications.count_by_language(LANGUAGE_HTML),
            cpp=self.applications.count_by_language(LANGUAGE_CPP),
            docker_yes=self.applications.count_docker(True),
            nginx_yes=self.applications.count_nginx(),
        )

    def list_languages(self) -> list[LanguageOut]:
        return [LanguageOut.model_validate(item) for item in self.languages.list_all()]

    def create_language(self, payload: LanguageCreate) -> LanguageOut:
        name = normalize_language(payload.name)
        if self.languages.get_by_name(name):
            raise ValidationError("name", "Esta linguagem já está cadastrada.")
        language = self.languages.create(name)
        self.db.commit()
        self.db.refresh(language)
        return LanguageOut.model_validate(language)
