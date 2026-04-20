"""Runtime configuration loaded from environment / .env.

All knobs live here. Nothing else reads `os.environ` directly.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Data sources ---
    open_meteo_base_url: str = Field(
        default="https://api.open-meteo.com/v1",
        alias="OPEN_METEO_BASE_URL",
    )
    open_meteo_ensemble_url: str = Field(
        default="https://ensemble-api.open-meteo.com/v1/ensemble",
        alias="OPEN_METEO_ENSEMBLE_URL",
    )
    meteostat_api_key: str | None = Field(default=None, alias="METEOSTAT_API_KEY")

    polymarket_gamma_url: str = Field(
        default="https://gamma-api.polymarket.com",
        alias="POLYMARKET_GAMMA_URL",
    )
    polymarket_clob_url: str = Field(
        default="https://clob.polymarket.com",
        alias="POLYMARKET_CLOB_URL",
    )

    # --- Execution ---
    live_trading: bool = Field(default=False, alias="LIVE_TRADING")
    polymarket_private_key: str | None = Field(default=None, alias="POLYMARKET_PRIVATE_KEY")
    polymarket_funder_address: str | None = Field(default=None, alias="POLYMARKET_FUNDER_ADDRESS")

    # --- Risk & sizing ---
    bankroll_usd: float = Field(default=1000.0, alias="BANKROLL_USD")
    kelly_fraction: float = Field(default=0.33, alias="KELLY_FRACTION")
    max_per_market_pct: float = Field(default=0.05, alias="MAX_PER_MARKET_PCT")
    daily_drawdown_kill_pct: float = Field(default=0.10, alias="DAILY_DRAWDOWN_KILL_PCT")
    min_edge_pct: float = Field(default=0.03, alias="MIN_EDGE_PCT")

    # --- Alerts ---
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")

    # --- Storage ---
    db_path: Path = Field(
        default=REPO_ROOT / "weather_alpha" / "data.sqlite",
        alias="WEATHER_ALPHA_DB_PATH",
    )

    # --- Scheduler cadences (seconds) ---
    market_snapshot_interval_s: int = Field(default=60, alias="MARKET_SNAPSHOT_INTERVAL_S")
    forecast_refresh_interval_s: int = Field(default=1800, alias="FORECAST_REFRESH_INTERVAL_S")
    edge_tick_interval_s: int = Field(default=120, alias="EDGE_TICK_INTERVAL_S")

    def assert_live_ready(self) -> None:
        """Fail fast if live trading is requested without credentials."""
        if not self.live_trading:
            return
        missing = [
            name
            for name, val in [
                ("POLYMARKET_PRIVATE_KEY", self.polymarket_private_key),
                ("POLYMARKET_FUNDER_ADDRESS", self.polymarket_funder_address),
            ]
            if not val
        ]
        if missing:
            raise RuntimeError(
                f"LIVE_TRADING=1 but required env vars missing: {', '.join(missing)}"
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
