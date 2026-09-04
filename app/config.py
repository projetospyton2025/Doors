from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Doors"
    app_env: str = "development"
    debug: bool = True
    app_secret_key: str = "altere-esta-chave-em-producao"
    database_url: str = "sqlite:///./data/doors.db"
    allowed_hosts: str = "*"
    doors_xlsx_path: str = "./Doors.xlsx"
    app_host: str = "127.0.0.1"
    app_port: int = 5333

    @property
    def data_dir(self) -> Path:
        path = BASE_DIR / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def exports_dir(self) -> Path:
        path = BASE_DIR / "exports"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def xlsx_path(self) -> Path:
        candidate = Path(self.doors_xlsx_path)
        if not candidate.is_absolute():
            candidate = BASE_DIR / candidate
        return candidate

    @property
    def host_list(self) -> list[str]:
        return [item.strip() for item in self.allowed_hosts.split(",") if item.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
