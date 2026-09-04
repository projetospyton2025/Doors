import re

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_text(value: str | None, *, max_length: int = 2000) -> str | None:
    if value is None:
        return None
    cleaned = _CONTROL_CHARS.sub("", str(value)).strip()
    if not cleaned:
        return None
    return cleaned[:max_length]
