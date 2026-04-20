-- weather_alpha storage schema. SQLite with WAL.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Polymarket markets we track.
CREATE TABLE IF NOT EXISTS markets (
    id                TEXT PRIMARY KEY,            -- Polymarket condition_id or slug
    slug              TEXT,
    question          TEXT NOT NULL,
    city              TEXT,
    country           TEXT,
    lat               REAL,
    lon               REAL,
    threshold_type    TEXT,                        -- 'high_temp_c', 'low_temp_c', 'precip_mm', 'wind_mph', ...
    threshold_value   REAL,
    comparator        TEXT,                        -- 'gte', 'lte'
    resolves_at       TEXT,                        -- ISO-8601 UTC
    yes_token_id      TEXT,
    no_token_id       TEXT,
    active            INTEGER NOT NULL DEFAULT 1,
    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_markets_active ON markets(active);
CREATE INDEX IF NOT EXISTS idx_markets_resolves_at ON markets(resolves_at);
CREATE INDEX IF NOT EXISTS idx_markets_city ON markets(city);

-- Per-tick order-book snapshots.
CREATE TABLE IF NOT EXISTS market_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id       TEXT NOT NULL,
    ts              TEXT NOT NULL,
    yes_bid         REAL,
    yes_ask         REAL,
    yes_mid         REAL,
    no_bid          REAL,
    no_ask          REAL,
    spread_pct      REAL,
    last_trade      REAL,
    volume_24h      REAL,
    bid_depth_1pct  REAL,
    ask_depth_1pct  REAL,
    FOREIGN KEY (market_id) REFERENCES markets(id)
);
CREATE INDEX IF NOT EXISTS idx_snap_market_ts ON market_snapshots(market_id, ts DESC);

-- Resolved outcomes (for historical error computation).
CREATE TABLE IF NOT EXISTS resolutions (
    market_id       TEXT PRIMARY KEY,
    resolved_yes    INTEGER NOT NULL,   -- 1 / 0
    resolved_at     TEXT NOT NULL,
    closing_yes     REAL,
    peak_yes        REAL,
    trough_yes      REAL,
    FOREIGN KEY (market_id) REFERENCES markets(id)
);

-- Ensemble weather forecasts, one row per (location, issued_at, member, valid_date, variable).
CREATE TABLE IF NOT EXISTS weather_forecasts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lat             REAL NOT NULL,
    lon             REAL NOT NULL,
    issued_at       TEXT NOT NULL,
    valid_date      TEXT NOT NULL,
    variable        TEXT NOT NULL,     -- 'temp_max_c', 'temp_min_c', 'precip_mm_sum', ...
    member          INTEGER NOT NULL,  -- 0 = deterministic, >=1 = ensemble members
    value           REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_forecast_loc_valid
    ON weather_forecasts(lat, lon, valid_date, variable, issued_at DESC);

-- Observed weather (Meteostat).
CREATE TABLE IF NOT EXISTS weather_actuals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lat             REAL NOT NULL,
    lon             REAL NOT NULL,
    observed_date   TEXT NOT NULL,
    variable        TEXT NOT NULL,
    value           REAL NOT NULL,
    UNIQUE (lat, lon, observed_date, variable)
);

-- Climate normals (long-run percentiles, e.g., 10y daily).
CREATE TABLE IF NOT EXISTS climate_normals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lat             REAL NOT NULL,
    lon             REAL NOT NULL,
    month           INTEGER NOT NULL,
    day             INTEGER NOT NULL,
    variable        TEXT NOT NULL,
    p10             REAL,
    p25             REAL,
    p50             REAL,
    p75             REAL,
    p90             REAL,
    std             REAL,
    mean            REAL,
    UNIQUE (lat, lon, month, day, variable)
);

-- Trade journal (paper). Written BEFORE simulated fill; status updated after.
CREATE TABLE IF NOT EXISTS trades_paper (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id       TEXT NOT NULL,
    side            TEXT NOT NULL,      -- 'BUY_YES', 'BUY_NO', 'SELL_YES', 'SELL_NO'
    size_usd        REAL NOT NULL,
    price           REAL NOT NULL,      -- fill price (0..1)
    status          TEXT NOT NULL,      -- 'QUEUED','FILLED','CANCELLED','SETTLED'
    pnl_usd         REAL,
    opened_at       TEXT NOT NULL,
    closed_at       TEXT,
    reason          TEXT,
    FOREIGN KEY (market_id) REFERENCES markets(id)
);
CREATE INDEX IF NOT EXISTS idx_paper_status ON trades_paper(status);

-- Trade journal (live). Same shape as paper plus broker refs.
CREATE TABLE IF NOT EXISTS trades_live (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id       TEXT NOT NULL,
    side            TEXT NOT NULL,
    size_usd        REAL NOT NULL,
    price           REAL NOT NULL,
    status          TEXT NOT NULL,
    broker_order_id TEXT,
    tx_hash         TEXT,
    pnl_usd         REAL,
    opened_at       TEXT NOT NULL,
    closed_at       TEXT,
    reason          TEXT,
    FOREIGN KEY (market_id) REFERENCES markets(id)
);
CREATE INDEX IF NOT EXISTS idx_live_status ON trades_live(status);

-- Kill-switch / operational state.
CREATE TABLE IF NOT EXISTS kill_switch (
    id              INTEGER PRIMARY KEY CHECK (id = 1),
    tripped         INTEGER NOT NULL DEFAULT 0,
    tripped_at      TEXT,
    reason          TEXT
);
INSERT OR IGNORE INTO kill_switch (id, tripped) VALUES (1, 0);
