from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("door", name="uq_applications_door"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    app_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(1000), nullable=False)
    door: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"), nullable=False, index=True)
    nginx: Mapped[str | None] = mapped_column(String(500), nullable=True)
    uses_docker: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    plan: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    github: Mapped[str | None] = mapped_column(String(500), nullable=True)
    drive: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, server_default=func.now(), onupdate=func.now()
    )

    language: Mapped["Language"] = relationship("Language", lazy="joined")
