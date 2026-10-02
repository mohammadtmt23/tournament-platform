from app.db import normalize_db_url


def test_postgres_prefixes_get_driver():
    assert normalize_db_url("postgres://u:p@h/db") == "postgresql+psycopg2://u:p@h/db"
    assert normalize_db_url("postgresql://u:p@h/db?sslmode=require") == \
        "postgresql+psycopg2://u:p@h/db?sslmode=require"


def test_already_qualified_and_sqlite_untouched():
    assert normalize_db_url("postgresql+psycopg2://u:p@h/db") == "postgresql+psycopg2://u:p@h/db"
    assert normalize_db_url("sqlite:///./dev.db") == "sqlite:///./dev.db"
