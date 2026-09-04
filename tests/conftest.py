from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setenv("DOORS_XLSX_PATH", str(tmp_path / "missing.xlsx"))
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "true")
    from app.config import get_settings

    get_settings.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


@pytest.fixture()
def sample_payload() -> dict:
    return {
        "app_name": "AudioTo-txt",
        "path": r"M:\Meu Drive\ProjetosPython\Audio\AudioTo-txt",
        "door": 5222,
        "language": "Python",
        "nginx": "https://marciofernandomaia.com.br/app",
        "docker": "Não",
        "plan": "work",
        "github": "",
        "drive": "",
    }
