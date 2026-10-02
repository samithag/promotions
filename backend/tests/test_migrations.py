from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings

BACKEND = Path(__file__).parent.parent


def test_migrations_create_every_table(tmp_path: Path, monkeypatch) -> None:
    url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    try:
        command.upgrade(Config(str(BACKEND / "alembic.ini")), "head")
    finally:
        get_settings.cache_clear()
    tables = set(inspect(create_engine(url)).get_table_names())
    assert {"banks", "promotions", "scrape_runs"} <= tables
