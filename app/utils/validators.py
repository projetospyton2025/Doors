from urllib.parse import urlparse

from app.utils.constants import (
    DOCKER_NO,
    DOCKER_YES,
    DOOR_MAX,
    DOOR_MIN,
    EXCEL_PLAN_ALIASES,
    LANGUAGE_ALIASES,
    LANGUAGE_HTML,
    Plan,
)
from app.utils.security import sanitize_text


class ValidationError(ValueError):
    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.message = message


def normalize_plan(value: str | None) -> str:
    cleaned = sanitize_text(value, max_length=40)
    if not cleaned:
        raise ValidationError("plan", "O plano é obrigatório.")
    key = EXCEL_PLAN_ALIASES.get(cleaned.lower())
    if not key:
        raise ValidationError("plan", "Plano inválido. Use Work, Personal ou Lotteries.")
    return key


def normalize_language(value: str | None) -> str:
    cleaned = sanitize_text(value, max_length=80)
    if not cleaned:
        raise ValidationError("language", "A linguagem é obrigatória.")
    alias = LANGUAGE_ALIASES.get(cleaned.lower())
    if alias:
        return alias
    if cleaned.lower() == "html":
        return LANGUAGE_HTML
    return cleaned


def normalize_docker(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    cleaned = sanitize_text(str(value) if value is not None else None, max_length=10)
    if cleaned is None:
        raise ValidationError("docker", "Informe se a aplicação utiliza Docker.")
    lowered = cleaned.lower()
    if lowered in {"sim", "yes", "true", "1", "s"}:
        return True
    if lowered in {"não", "nao", "no", "false", "0", "n"}:
        return False
    raise ValidationError("docker", "Docker deve ser Sim ou Não.")


def docker_label(uses_docker: bool) -> str:
    return DOCKER_YES if uses_docker else DOCKER_NO


def normalize_door(value: int | str | None) -> int:
    if value is None or value == "":
        raise ValidationError("door", "A porta é obrigatória.")
    try:
        door = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValidationError("door", "A porta deve ser um número inteiro.") from exc
    if door < DOOR_MIN or door > DOOR_MAX:
        raise ValidationError("door", f"A porta deve estar entre {DOOR_MIN} e {DOOR_MAX}.")
    return door


def normalize_required_name(value: str | None, field: str, label: str) -> str:
    cleaned = sanitize_text(value, max_length=200)
    if not cleaned:
        raise ValidationError(field, f"{label} é obrigatório.")
    return cleaned


def normalize_path(value: str | None) -> str:
    cleaned = sanitize_text(value, max_length=1000)
    if not cleaned:
        raise ValidationError("path", "O caminho da aplicação é obrigatório.")
    if any(token in cleaned for token in ("\n", "\r")):
        raise ValidationError("path", "O caminho informado é inválido.")
    return cleaned


def normalize_optional_link(value: str | None, field: str) -> str | None:
    cleaned = sanitize_text(value, max_length=500)
    if not cleaned:
        return None
    if cleaned.lower().startswith(("http://", "https://")):
        parsed = urlparse(cleaned)
        if not parsed.netloc:
            raise ValidationError(field, "URL inválida.")
    return cleaned


def plan_enum(value: str) -> Plan:
    return Plan(normalize_plan(value))
