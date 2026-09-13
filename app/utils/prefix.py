from fastapi import Request

PUBLIC_PREFIX = "/doors"


def normalize_prefix(value: str | None) -> str:
    cleaned = (value or "").rstrip("/")
    if cleaned.lower() == PUBLIC_PREFIX:
        return PUBLIC_PREFIX
    return cleaned


def resolve_prefix(request: Request) -> str:
    header = normalize_prefix(request.headers.get("x-forwarded-prefix"))
    if header:
        return header
    path = (request.url.path or "").lower()
    if path == PUBLIC_PREFIX or path.startswith(f"{PUBLIC_PREFIX}/"):
        return PUBLIC_PREFIX
    return normalize_prefix(str(request.scope.get("root_path") or ""))
