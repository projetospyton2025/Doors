from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.utils.constants import DOCKER_NO, DOCKER_YES


class ApplicationCreate(BaseModel):
    app_name: str = Field(..., min_length=1, max_length=200)
    path: str = Field(..., min_length=1, max_length=1000)
    door: int | str
    language: str = Field(..., min_length=1, max_length=80)
    nginx: str | None = None
    docker: str | bool
    plan: str = Field(..., min_length=1, max_length=40)
    github: str | None = None
    drive: str | None = None


class ApplicationUpdate(ApplicationCreate):
    pass


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    app_name: str
    path: str
    door: int
    language: str
    nginx: str | None
    docker: Literal["Sim", "Não"]
    uses_docker: bool
    uses_nginx: bool
    plan: str
    plan_label: str
    github: str | None
    drive: str | None
    created_at: datetime
    updated_at: datetime


class ApplicationFilters(BaseModel):
    q: str | None = None
    plan: str | None = None
    language: str | None = None
    docker: str | None = None
    nginx: str | None = None
    sort: str = "app_name"
    order: Literal["asc", "desc"] = "asc"
    page: int = 1
    page_size: int = 10


class LanguageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LanguageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


class DashboardStats(BaseModel):
    total: int
    work: int
    personal: int
    lotteries: int
    python: int
    html: int
    docker_yes: int
    nginx_yes: int


class PaginatedApplications(BaseModel):
    items: list[ApplicationOut]
    total: int
    page: int
    page_size: int
    pages: int


class MessageOut(BaseModel):
    message: str


def docker_to_label(uses_docker: bool) -> str:
    return DOCKER_YES if uses_docker else DOCKER_NO
