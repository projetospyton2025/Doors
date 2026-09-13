import re
from enum import Enum

DOOR_MIN = 1
DOOR_MAX = 65535

# Apps filhas chamadas pela central LoteriasExtras-Conferencias — não listar/cadastrar.
SATELLITE_APP_PATTERN = re.compile(
    r"^LoteriasExtras-Conferencias-.+$",
    re.IGNORECASE,
)

DOCKER_YES = "Sim"
DOCKER_NO = "Não"

LANGUAGE_PYTHON = "Python"
LANGUAGE_HTML = "HTML"

EXCEL_PLAN_ALIASES = {
    "work": "work",
    "personal": "personal",
    "lotteries": "lotteries",
    "loterries": "lotteries",
}

LANGUAGE_ALIASES = {
    "python": LANGUAGE_PYTHON,
    "html": LANGUAGE_HTML,
    "html ": LANGUAGE_HTML,
}


class Plan(str, Enum):
    WORK = "work"
    PERSONAL = "personal"
    LOTTERIES = "lotteries"


PLANS = (
    {"key": Plan.WORK.value, "label": "Work", "excel": "Work"},
    {"key": Plan.PERSONAL.value, "label": "Personal", "excel": "Personal"},
    {"key": Plan.LOTTERIES.value, "label": "Lotteries", "excel": "Loterries"},
)

PLAN_LABELS = {item["key"]: item["label"] for item in PLANS}

EXPORT_COLUMNS = (
    "PLAN",
    "APP NAME",
    "PATH",
    "DOOR",
    "LANGUAGE",
    "REMOTO",
    "DOCKER",
    "GITHUB",
    "DRIVE",
)

# Remoto = URL pública de acesso (coluna Remoto do links.xlsx; no Doors.xlsx era NGINX)
REDIRECT_LINK_TYPES = (
    {"key": "remoto", "label": "REMOTO", "excel": "REMOTO"},
    {"key": "github", "label": "GITHUB", "excel": "ACCOUNT → GITHUB"},
    {"key": "drive", "label": "DRIVE", "excel": "ACCOUNT → DRIVE"},
)

REDIRECT_LINK_LABELS = {item["key"]: item["label"] for item in REDIRECT_LINK_TYPES}


def is_satellite_app(app_name: str) -> bool:
    """True para apps filhas de conferência (ex.: ...-MegaSena); a central fica de fora."""
    return bool(SATELLITE_APP_PATTERN.match((app_name or "").strip()))
