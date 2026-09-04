from enum import Enum

DOOR_MIN = 1
DOOR_MAX = 65535

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
    "NGINX",
    "DOCKER",
    "GITHUB",
    "DRIVE",
)
