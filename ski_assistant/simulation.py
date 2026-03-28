"""
Avoriaz Ski Simulation Engine
==============================
Snow quality, crowd dynamics, and enjoyment modeling for the
Portes du Soleil ski area — active through April 4th.

Architecture
------------
  SnowModel     → altitude + orientation + temperature + sun exposure
  CrowdModel    → agent-based with lift bottlenecks + skill clustering + noise
  EnjoymentFn   → weighted composite scoring
  RunConditions → full snapshot for any run × datetime
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

# ──────────────────────────────────────────────────────────────────────────────
# ENUMERATIONS
# ──────────────────────────────────────────────────────────────────────────────

class Difficulty(Enum):
    GREEN  = "green"
    BLUE   = "blue"
    RED    = "red"
    BLACK  = "black"

class Orientation(Enum):
    N  = "N"
    NE = "NE"
    E  = "E"
    SE = "SE"
    S  = "S"
    SW = "SW"
    W  = "W"
    NW = "NW"

SEASON_END = datetime(2026, 4, 4, 17, 0)

# ──────────────────────────────────────────────────────────────────────────────
# DATA MODELS
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SkiRun:
    name:         str
    difficulty:   Difficulty
    altitude_m:   int          # average altitude (metres)
    orientation:  Orientation
    length_km:    float
    primary_lift: str
    popularity:   float        # base demand 0–1
    flow_score:   float        # run fluidity 0–1
    notes:        str = ""

@dataclass
class RunConditions:
    run:                SkiRun
    snow_score:         float   # 0–100
    crowd_level:        float   # 0–1
    crowd_label:        str     # Low / Medium / High
    enjoyment_score:    float   # 0–100
    temperature_c:      float
    snow_surface:       str     # powder / groomed / softening / slushy / icy
    timestamp:          datetime
    recommendation_reason: str = ""

# ──────────────────────────────────────────────────────────────────────────────
# AVORIAZ RUN DATABASE  (12 runs across the Portes du Soleil sector)
# ──────────────────────────────────────────────────────────────────────────────

AVORIAZ_RUNS: List[SkiRun] = [
    SkiRun(
        "Combe de Chavannes", Difficulty.RED, 2050, Orientation.N, 3.2,
        "Chavannes Express", popularity=0.65, flow_score=0.82,
        notes="Classic summit red; N-facing wall holds powder long after snowfall",
    ),
    SkiRun(
        "Arare", Difficulty.BLUE, 1900, Orientation.E, 2.1,
        "Arare Chairlift", popularity=0.70, flow_score=0.68,
        notes="Wide groomed blue; morning sun burns off ice without cooking the snow",
    ),
    SkiRun(
        "La Schuss", Difficulty.BLACK, 2150, Orientation.N, 2.8,
        "Chavannes Express", popularity=0.35, flow_score=0.75,
        notes="Sustained steep N-facing line; superb dry snow but demands advanced skill",
    ),
    SkiRun(
        "Lindarets Valley", Difficulty.BLUE, 1700, Orientation.S, 2.5,
        "Lindarets Lift", popularity=0.78, flow_score=0.60,
        notes="Scenic low-altitude valley; S-facing = slushy by noon in late March",
    ),
    SkiRun(
        "Mossettes", Difficulty.RED, 2050, Orientation.W, 3.5,
        "Mossettes Lift", popularity=0.55, flow_score=0.78,
        notes="Long flowing red; excellent mornings, afternoon sun hits from 13:30",
    ),
    SkiRun(
        "Fornet", Difficulty.RED, 1950, Orientation.NE, 2.2,
        "Fornet T-Bar", popularity=0.28, flow_score=0.85,
        notes="Hidden gem; NE orientation + low footfall = consistently excellent conditions",
    ),
    SkiRun(
        "Prolys", Difficulty.BLUE, 1850, Orientation.N, 1.8,
        "Crêtes Chairlift", popularity=0.82, flow_score=0.55,
        notes="Most popular blue; high throughput near village creates congestion",
    ),
    SkiRun(
        "Crêtes", Difficulty.BLUE, 2000, Orientation.E, 2.0,
        "Crêtes Chairlift", popularity=0.60, flow_score=0.72,
        notes="Ridgeline run with panoramic views; shares lift with Prolys but less traffic",
    ),
    SkiRun(
        "Chamois", Difficulty.RED, 2200, Orientation.N, 4.1,
        "Chavannes Express", popularity=0.40, flow_score=0.88,
        notes="Highest-altitude red in sector; longest run, rarely crowded — hidden gem",
    ),
    SkiRun(
        "Stade Slalom", Difficulty.BLACK, 2200, Orientation.N, 1.5,
        "Chavannes Express", popularity=0.30, flow_score=0.65,
        notes="Race-course groomed pitch; technical but perfectly prepared",
    ),
    SkiRun(
        "Combe du Machon", Difficulty.RED, 1800, Orientation.S, 2.8,
        "Machon Lift", popularity=0.50, flow_score=0.70,
        notes="Mid-mountain red; S-facing means rapid snow deterioration after 11:30",
    ),
    SkiRun(
        "Super Morzine", Difficulty.BLUE, 1650, Orientation.S, 3.0,
        "Super Morzine Gondola", popularity=0.68, flow_score=0.58,
        notes="Low-altitude connector to Morzine; scenic but snow quality marginal by April",
    ),
]

RUNS_BY_NAME: Dict[str, SkiRun] = {r.name: r for r in AVORIAZ_RUNS}

# ──────────────────────────────────────────────────────────────────────────────
# WEATHER PROFILE  (March 28 – April 4, 2026)
# ──────────────────────────────────────────────────────────────────────────────
# Format: date_str → (base_temp_°C at 2000m, snowfall_last_24h_cm, cloud_cover_0–1)

DAILY_WEATHER: Dict[str, Tuple[float, float, float]] = {
    "2026-03-28": (-4.0,  8.0, 0.60),   # fresh snowfall, overcast
    "2026-03-29": (-3.5,  2.0, 0.30),   # clearing, light overnight snow
    "2026-03-30": (-2.0,  0.0, 0.10),   # sunny bluebird
    "2026-03-31": (-1.5,  0.0, 0.20),   # warm, mostly clear
    "2026-04-01": (-5.0, 15.0, 0.95),   # storm day — heavy new snow
    "2026-04-02": (-4.5,  5.0, 0.50),   # clearing after storm
    "2026-04-03": (-2.5,  0.0, 0.20),   # spring bluebird
    "2026-04-04": (-1.0,  0.0, 0.10),   # warmest day — season finale
}

def get_weather(dt: datetime) -> Tuple[float, float, float]:
    """Return (base_temp, snowfall_cm, cloud_cover) for a given datetime."""
    key = dt.strftime("%Y-%m-%d")
    return DAILY_WEATHER.get(key, (-3.0, 0.0, 0.30))

# ──────────────────────────────────────────────────────────────────────────────
# SNOW QUALITY MODEL
# ──────────────────────────────────────────────────────────────────────────────

# Sun-exposure profile per orientation (azimuth intensity at each hour 0–23)
# Values represent solar intensity 0–1 for a clear-sky March/April alpine day.
_SUN_PROFILES: Dict[Orientation, Dict[int, float]] = {
    Orientation.N:  {h: 0.04  for h in range(24)},
    Orientation.NE: {
        **{h: 0.0 for h in range(0, 7)},
        7: 0.30, 8: 0.65, 9: 0.90, 10: 0.85, 11: 0.55,
        12: 0.25, 13: 0.10, **{h: 0.04 for h in range(14, 24)},
    },
    Orientation.E: {
        **{h: 0.0 for h in range(0, 8)},
        8: 0.50, 9: 0.85, 10: 1.00, 11: 0.90, 12: 0.60,
        13: 0.25, **{h: 0.05 for h in range(14, 24)},
    },
    Orientation.SE: {
        **{h: 0.0 for h in range(0, 9)},
        9: 0.55, 10: 0.85, 11: 1.00, 12: 0.95, 13: 0.75,
        14: 0.40, 15: 0.15, **{h: 0.04 for h in range(16, 24)},
    },
    Orientation.S: {
        **{h: 0.0 for h in range(0, 10)},
        10: 0.60, 11: 0.90, 12: 1.00, 13: 1.00, 14: 0.85,
        15: 0.55, 16: 0.20, **{h: 0.04 for h in range(17, 24)},
    },
    Orientation.SW: {
        **{h: 0.0 for h in range(0, 12)},
        12: 0.30, 13: 0.65, 14: 0.90, 15: 1.00, 16: 0.85,
        17: 0.40, **{h: 0.04 for h in range(18, 24)},
    },
    Orientation.W: {
        **{h: 0.0 for h in range(0, 13)},
        13: 0.35, 14: 0.70, 15: 0.95, 16: 1.00, 17: 0.70,
        **{h: 0.10 for h in range(18, 24)},
    },
    Orientation.NW: {
        **{h: 0.0 for h in range(0, 14)},
        14: 0.20, 15: 0.45, 16: 0.70, 17: 0.55, 18: 0.20,
        **{h: 0.04 for h in range(19, 24)},
    },
}


def sun_exposure(orientation: Orientation, hour: int, cloud_cover: float) -> float:
    """
    Effective solar intensity on a slope face at a given hour.
    Clouds cut up to 75% of direct radiation.
    Returns 0–1.
    """
    profile = _SUN_PROFILES.get(orientation, {})
    raw = profile.get(hour, 0.04)
    return raw * (1.0 - cloud_cover * 0.75)


def altitude_factor(altitude_m: int) -> float:
    """
    Higher altitude → better snow retention.
    Normalized so 1800m = 1.0, 2200m ≈ 1.18.
    """
    return 1.0 + (altitude_m - 1800) / 2200.0


def temperature_factor(temp_c: float) -> float:
    """
    Ideal snow texture: −8 to −2 °C → factor ≈ 1.0.
    Warmer → softening/slush.  Much colder → wind-slab/brittle.
    """
    if   temp_c < -15: return 0.72
    elif temp_c < -8:  return 0.85 + (temp_c + 15) * 0.022
    elif temp_c < -2:  return 1.00
    elif temp_c < 0:   return 1.00 - (temp_c + 2) * 0.07
    elif temp_c < 3:   return 0.86 - temp_c * 0.09
    else:              return max(0.38, 0.59 - temp_c * 0.05)


def diurnal_temp(base_temp: float, hour: int) -> float:
    """Daily temperature cycle: minimum at 07:00, peak at 14:00 (±4 °C swing)."""
    phase = (hour - 7) / 24.0 * 2 * math.pi
    return base_temp + 4.0 * math.sin(phase)


def snow_surface_label(
    snow_score: float, hour: int,
    orientation: Orientation, cloud_cover: float,
) -> str:
    """Human-readable snow surface description."""
    sun = sun_exposure(orientation, hour, cloud_cover)
    if snow_score > 80 and sun < 0.15:
        return "powder"
    elif snow_score > 65 and sun < 0.35:
        return "groomed / firm"
    elif snow_score > 50 and sun < 0.60:
        return "softening"
    elif sun >= 0.60:
        return "slushy"
    elif snow_score < 38:
        return "icy / wind-packed"
    else:
        return "wind-packed"


def compute_snow_score(
    run: SkiRun,
    dt: datetime,
    snowfall_cm: float,
    base_temp: float,
    cloud_cover: float,
    seed: Optional[int] = None,
) -> Tuple[float, str]:
    """
    Core snow quality index (0–100).

    Components
    ----------
    base_pack       — late-season snow depth baseline (65–70 typical)
    snowfall_bonus  — up to +25 pts for fresh powder
    altitude_factor — higher is always better
    temp_factor     — sweet spot −8 to −2 °C
    sun_damage      — cumulative degradation from slope orientation × sun hours
    age_penalty     — older snow pack slowly degrades between storms
    noise           — ±3 pts stochastic variation

    Returns
    -------
    (score: float, surface_label: str)
    """
    rng = np.random.default_rng(seed if seed is not None else int(dt.timestamp()) % 99991)

    hour        = dt.hour
    temp_now    = diurnal_temp(base_temp, hour)
    base_pack   = 67.0
    sf_bonus    = min(25.0, snowfall_cm * 1.75)
    alt_f       = altitude_factor(run.altitude_m)
    temp_f      = temperature_factor(temp_now)

    # Cumulative sun damage from 08:00 to current hour (each hour costs up to 4 pts)
    sun_dmg = sum(
        sun_exposure(run.orientation, h, cloud_cover) * 4.0
        for h in range(8, min(hour + 1, 18))
    )

    # Days since last meaningful snowfall
    ref_date    = datetime(2026, 3, 28).date()
    days_elapsed = max(0, (dt.date() - ref_date).days)
    age_penalty = 0.0 if snowfall_cm > 3 else days_elapsed * 2.2

    raw   = (base_pack + sf_bonus) * alt_f * temp_f - sun_dmg - age_penalty
    noise = float(rng.normal(0, 2.8))
    score = float(np.clip(raw + noise, 0.0, 100.0))

    return round(score, 1), snow_surface_label(score, hour, run.orientation, cloud_cover)


# ──────────────────────────────────────────────────────────────────────────────
# CROWD MODEL  (Agent-Based)
# ──────────────────────────────────────────────────────────────────────────────

# Lift congestion at peak hours  (0 = no queue, 1 = gridlock)
LIFT_CONGESTION: Dict[str, float] = {
    "Chavannes Express":      0.92,  # primary mountain access — always busy
    "Crêtes Chairlift":       0.76,
    "Arare Chairlift":        0.65,
    "Lindarets Lift":         0.70,
    "Mossettes Lift":         0.55,
    "Fornet T-Bar":           0.24,  # remote, low traffic
    "Machon Lift":            0.44,
    "Super Morzine Gondola":  0.60,
}

# Skill-level proportion on each run type (drives beginner overflow pressure)
SKILL_CLUSTER: Dict[Difficulty, Dict[str, float]] = {
    Difficulty.GREEN: {"beginner": 0.60, "intermediate": 0.35, "advanced": 0.05},
    Difficulty.BLUE:  {"beginner": 0.40, "intermediate": 0.45, "advanced": 0.15},
    Difficulty.RED:   {"beginner": 0.05, "intermediate": 0.55, "advanced": 0.40},
    Difficulty.BLACK: {"beginner": 0.00, "intermediate": 0.15, "advanced": 0.85},
}

# Hourly crowd multiplier (slopes open 09:00–17:00 in Avoriaz)
_HOUR_CROWD: Dict[int, float] = {
    8: 0.25, 9: 0.72, 10: 0.95, 11: 1.00,
    12: 0.62, 13: 0.55, 14: 0.90, 15: 0.82,
    16: 0.50, 17: 0.20,
}

# Day-of-week tourist factor  (0=Mon … 6=Sun)
_DOW_FACTOR: Dict[int, float] = {
    0: 0.72, 1: 0.68, 2: 0.70, 3: 0.68,
    4: 0.83, 5: 1.00, 6: 0.91,
}


def compute_crowd_level(
    run: SkiRun,
    dt: datetime,
    tourist_multiplier: float = 1.0,
    seed: Optional[int] = None,
) -> Tuple[float, str]:
    """
    Agent-based crowd estimate (0–1) for a run at a given time.

    Factors
    -------
    base popularity × time-of-day × day-of-week × tourist surge
    + lift bottleneck overspill pressure
    + skill-level clustering (beginners flood easy runs)
    + stochastic noise ±10 %

    Returns
    -------
    (crowd_level: float 0–1, label: "Low" | "Medium" | "High")
    """
    rng = np.random.default_rng(seed if seed is not None else int(dt.timestamp()) % 88887)

    hour = dt.hour
    time_m   = _HOUR_CROWD.get(hour, 0.0)
    if time_m == 0.0:
        return 0.0, "Low"

    dow_m    = _DOW_FACTOR.get(dt.weekday(), 0.72)
    lift_c   = LIFT_CONGESTION.get(run.primary_lift, 0.50)
    skill    = SKILL_CLUSTER.get(run.difficulty, {})

    base     = run.popularity * time_m * dow_m * tourist_multiplier
    lift_p   = lift_c * 0.18       # congestion pushes people onto nearby runs
    skill_p  = skill.get("beginner", 0.0) * 0.14  # beginners cluster on blues

    raw      = base + lift_p + skill_p
    noise    = float(rng.normal(0.0, 0.07))
    crowd    = float(np.clip(raw + noise, 0.0, 1.0))

    label = "Low" if crowd < 0.35 else ("Medium" if crowd < 0.62 else "High")
    return round(crowd, 3), label


# ──────────────────────────────────────────────────────────────────────────────
# ENJOYMENT FUNCTION
# ──────────────────────────────────────────────────────────────────────────────

def compute_enjoyment(
    run: SkiRun,
    snow_score: float,
    crowd_level: float,
    user_prefs: Optional[Dict] = None,
) -> float:
    """
    Composite enjoyment score (0–100).

    Default weights
    ---------------
    snow_quality  35 %  — primary quality driver
    crowd_penalty 30 %  — enormous impact on flow and fun
    run_length    15 %  — longer = more satisfying laps
    run_flow      20 %  — natural rhythm / terrain shape

    User preferences shift snow and crowd weights by up to +15 pp each.
    """
    prefs = user_prefs or {}

    w_snow  = 0.35 + prefs.get("prioritize_snow", 0.0) * 0.15
    w_crowd = 0.30 + prefs.get("avoid_crowds",    0.0) * 0.15
    w_len   = 0.15
    w_flow  = 0.20

    # Normalise so weights always sum to 1.0
    total = w_snow + w_crowd + w_len + w_flow
    w_snow  /= total;  w_crowd /= total
    w_len   /= total;  w_flow  /= total

    c_snow  = snow_score
    c_crowd = (1.0 - crowd_level) * 100.0
    c_len   = min(100.0, run.length_km / 4.5 * 100.0)
    c_flow  = run.flow_score * 100.0

    score = (
        w_snow  * c_snow  +
        w_crowd * c_crowd +
        w_len   * c_len   +
        w_flow  * c_flow
    )
    return round(float(np.clip(score, 0.0, 100.0)), 1)


# ──────────────────────────────────────────────────────────────────────────────
# FULL CONDITION SNAPSHOT
# ──────────────────────────────────────────────────────────────────────────────

def get_run_conditions(
    run: SkiRun,
    dt: datetime,
    tourist_multiplier: float = 1.0,
    user_prefs: Optional[Dict] = None,
    seed: Optional[int] = None,
) -> RunConditions:
    """Full condition snapshot for one run at one moment in time."""
    base_temp, snowfall_cm, cloud_cover = get_weather(dt)

    snow_score, surface = compute_snow_score(
        run, dt, snowfall_cm, base_temp, cloud_cover, seed
    )
    crowd_level, crowd_label = compute_crowd_level(
        run, dt, tourist_multiplier, seed
    )
    enjoyment = compute_enjoyment(run, snow_score, crowd_level, user_prefs)

    return RunConditions(
        run=run,
        snow_score=snow_score,
        crowd_level=crowd_level,
        crowd_label=crowd_label,
        enjoyment_score=enjoyment,
        temperature_c=round(diurnal_temp(base_temp, dt.hour), 1),
        snow_surface=surface,
        timestamp=dt,
    )


def get_all_conditions(
    dt: datetime,
    tourist_multiplier: float = 1.0,
    user_prefs: Optional[Dict] = None,
    seed: Optional[int] = None,
) -> List[RunConditions]:
    """
    Return conditions for all 12 runs, sorted by enjoyment score (best first).
    """
    return sorted(
        [
            get_run_conditions(r, dt, tourist_multiplier, user_prefs, seed)
            for r in AVORIAZ_RUNS
        ],
        key=lambda rc: rc.enjoyment_score,
        reverse=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# TIME-SERIES BUILDER
# ──────────────────────────────────────────────────────────────────────────────

def build_daily_series(
    date: datetime,
    hours: Optional[List[int]] = None,
    tourist_multiplier: float = 1.0,
    seed: int = 42,
) -> Dict[int, List[RunConditions]]:
    """
    Returns a dict mapping hour → sorted RunConditions list for a full day.
    Default hours: 08 through 16 inclusive.
    """
    hours = hours or list(range(8, 17))
    series: Dict[int, List[RunConditions]] = {}
    for h in hours:
        dt = date.replace(hour=h, minute=0, second=0, microsecond=0)
        series[h] = get_all_conditions(dt, tourist_multiplier, seed=seed + h)
    return series
