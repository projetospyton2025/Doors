"""Cria as tabelas e aplica a carga inicial do banco."""

from app.config import get_settings
from app.database.init_db import init_db
from app.database.session import init_engine


def main() -> None:
    get_settings().data_dir
    get_settings().exports_dir
    init_engine()
    init_db()
    print("Banco inicializado em", get_settings().database_url)


if __name__ == "__main__":
    main()
