from sqlalchemy import Select, String, and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.language import Language

SORTABLE = {
    "app_name": Application.app_name,
    "path": Application.path,
    "door": Application.door,
    "language": Language.name,
    "nginx": Application.nginx,
    "docker": Application.uses_docker,
    "plan": Application.plan,
    "github": Application.github,
    "drive": Application.drive,
    "created_at": Application.created_at,
    "updated_at": Application.updated_at,
}


class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def _base_query(self) -> Select[tuple[Application]]:
        return select(Application).join(Language)

    def _apply_filters(
        self,
        stmt: Select[tuple[Application]],
        *,
        q: str | None = None,
        plan: str | None = None,
        language: str | None = None,
        uses_docker: bool | None = None,
        uses_nginx: bool | None = None,
    ) -> Select[tuple[Application]]:
        conditions = []
        if q:
            term = f"%{q.strip()}%"
            conditions.append(
                or_(
                    Application.app_name.ilike(term),
                    Application.path.ilike(term),
                    Application.nginx.ilike(term),
                    Application.github.ilike(term),
                    Application.drive.ilike(term),
                    Language.name.ilike(term),
                    Application.plan.ilike(term),
                    func.cast(Application.door, String).ilike(term),
                )
            )
        if plan:
            conditions.append(Application.plan == plan)
        if language:
            conditions.append(Language.name == language)
        if uses_docker is not None:
            conditions.append(Application.uses_docker.is_(uses_docker))
        if uses_nginx is True:
            conditions.append(and_(Application.nginx.is_not(None), Application.nginx != ""))
        if uses_nginx is False:
            conditions.append(or_(Application.nginx.is_(None), Application.nginx == ""))
        # Oculta apps filhas da central de conferências (LoteriasExtras-Conferencias-*)
        conditions.append(~Application.app_name.ilike("LoteriasExtras-Conferencias-%"))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        return stmt

    def list_filtered(
        self,
        *,
        q: str | None = None,
        plan: str | None = None,
        language: str | None = None,
        uses_docker: bool | None = None,
        uses_nginx: bool | None = None,
        sort: str = "app_name",
        order: str = "asc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Application], int]:
        stmt = self._apply_filters(
            self._base_query(),
            q=q,
            plan=plan,
            language=language,
            uses_docker=uses_docker,
            uses_nginx=uses_nginx,
        )
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        column = SORTABLE.get(sort, Application.app_name)
        stmt = stmt.order_by(column.desc() if order == "desc" else column.asc())
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        items = list(self.db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all())
        return items, total

    def list_all_filtered(
        self,
        *,
        q: str | None = None,
        plan: str | None = None,
        language: str | None = None,
        uses_docker: bool | None = None,
        uses_nginx: bool | None = None,
        sort: str = "app_name",
        order: str = "asc",
    ) -> list[Application]:
        stmt = self._apply_filters(
            self._base_query(),
            q=q,
            plan=plan,
            language=language,
            uses_docker=uses_docker,
            uses_nginx=uses_nginx,
        )
        column = SORTABLE.get(sort, Application.app_name)
        stmt = stmt.order_by(column.desc() if order == "desc" else column.asc())
        return list(self.db.scalars(stmt).all())

    def get(self, application_id: int) -> Application | None:
        return self.db.get(Application, application_id)

    def get_by_door(self, door: int, exclude_id: int | None = None) -> Application | None:
        stmt = select(Application).where(Application.door == door)
        if exclude_id is not None:
            stmt = stmt.where(Application.id != exclude_id)
        return self.db.scalar(stmt)

    def create(self, application: Application) -> Application:
        self.db.add(application)
        self.db.flush()
        self.db.refresh(application)
        return application

    def delete(self, application: Application) -> None:
        self.db.delete(application)

    def _visible(self):
        return ~Application.app_name.ilike("LoteriasExtras-Conferencias-%")

    def count_all(self) -> int:
        return (
            self.db.scalar(select(func.count(Application.id)).where(self._visible()))
            or 0
        )

    def count_by_plan(self, plan: str) -> int:
        return (
            self.db.scalar(
                select(func.count(Application.id)).where(
                    and_(Application.plan == plan, self._visible())
                )
            )
            or 0
        )

    def count_by_language(self, language_name: str) -> int:
        return (
            self.db.scalar(
                select(func.count(Application.id))
                .join(Language)
                .where(and_(Language.name == language_name, self._visible()))
            )
            or 0
        )

    def count_docker(self, uses_docker: bool) -> int:
        return (
            self.db.scalar(
                select(func.count(Application.id)).where(
                    and_(Application.uses_docker.is_(uses_docker), self._visible())
                )
            )
            or 0
        )

    def count_nginx(self) -> int:
        return (
            self.db.scalar(
                select(func.count(Application.id)).where(
                    and_(
                        Application.nginx.is_not(None),
                        Application.nginx != "",
                        self._visible(),
                    )
                )
            )
            or 0
        )
