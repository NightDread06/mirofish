"""SQLite engine + schema bootstrap."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from weather_alpha.config import get_settings


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{settings.db_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    init_db(engine)
    return engine


def init_db(engine: Engine) -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with engine.begin() as conn:
        for stmt in _split_statements(sql):
            if stmt.strip():
                conn.exec_driver_sql(stmt)


def _split_statements(sql: str) -> list[str]:
    # Drop `-- ...` line comments first so stray semicolons in comments don't break the split.
    cleaned = "\n".join(
        line.split("--", 1)[0] for line in sql.splitlines()
    )
    return [s for s in cleaned.split(";") if s.strip()]


def reset_engine_cache() -> None:
    """For tests: drop cached engine so a new DB path takes effect."""
    get_engine.cache_clear()
