"""Isolate tests from any real .env and give each test its own SQLite file."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Neutralize any project .env before config is first imported.
os.environ.setdefault("OPEN_METEO_BASE_URL", "https://test.invalid/v1")
os.environ.setdefault("OPEN_METEO_ENSEMBLE_URL", "https://test.invalid/ensemble")
os.environ.setdefault("POLYMARKET_GAMMA_URL", "https://test.invalid/gamma")
os.environ.setdefault("POLYMARKET_CLOB_URL", "https://test.invalid/clob")
os.environ["LIVE_TRADING"] = "0"
os.environ["BANKROLL_USD"] = "1000"
os.environ["MIN_EDGE_PCT"] = "0.03"


@pytest.fixture(autouse=True)
def fresh_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point the settings + engine cache at a per-test SQLite file."""
    from weather_alpha import config as cfg
    from weather_alpha.storage import db

    monkeypatch.setenv("WEATHER_ALPHA_DB_PATH", str(tmp_path / "test.sqlite"))
    cfg.get_settings.cache_clear()
    db.get_engine.cache_clear()
    yield
    cfg.get_settings.cache_clear()
    db.get_engine.cache_clear()
