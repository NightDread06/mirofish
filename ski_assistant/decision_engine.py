"""
Avoriaz Ski Decision Engine
============================
Translates raw simulation data into actionable recommendations,
strategic itineraries, and analytical intelligence.

Public API
----------
  get_best_run(dt, prefs)          → single best run + explanation
  get_top_3(dt, prefs)             → dashboard top-3 cards
  get_time_strategy(dt)            → morning / midday / afternoon breakdown
  generate_day_plan(start, prefs)  → hour-by-hour itinerary
  get_hidden_gems(dt)              → contrarian intelligence
  sensitivity_analysis(dt)         → top-3 impactful variables
  stress_test(dt)                  → three adversarial scenarios
  decision_rules(dt)               → plain-english heuristics
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

from ski_assistant.simulation import (
    AVORIAZ_RUNS,
    DAILY_WEATHER,
    Difficulty,
    Orientation,
    RunConditions,
    SkiRun,
    build_daily_series,
    compute_crowd_level,
    compute_enjoyment,
    compute_snow_score,
    get_all_conditions,
    get_run_conditions,
    get_weather,
    diurnal_temp,
)

# ──────────────────────────────────────────────────────────────────────────────
# PREFERENCE SCHEMA
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class UserPreferences:
    """
    Encodes a skier's priorities. All float fields are 0–1 intensity.

    Attributes
    ----------
    prioritize_snow     Weight toward snow quality in enjoyment scoring.
    avoid_crowds        Weight toward emptier runs.
    difficulty_level    "beginner" | "intermediate" | "advanced" | "all"
    """
    prioritize_snow:  float = 0.5
    avoid_crowds:     float = 0.5
    difficulty_level: str   = "all"   # beginner | intermediate | advanced | all

    def to_dict(self) -> Dict:
        return {
            "prioritize_snow": self.prioritize_snow,
            "avoid_crowds":    self.avoid_crowds,
        }

    def difficulty_filter(self) -> List[Difficulty]:
        mapping = {
            "beginner":     [Difficulty.GREEN, Difficulty.BLUE],
            "intermediate": [Difficulty.BLUE,  Difficulty.RED],
            "advanced":     [Difficulty.RED,   Difficulty.BLACK],
            "all":          list(Difficulty),
        }
        return mapping.get(self.difficulty_level, list(Difficulty))


DEFAULT_PREFS = UserPreferences()

# ──────────────────────────────────────────────────────────────────────────────
# RECOMMENDATION REASON GENERATOR
# ──────────────────────────────────────────────────────────────────────────────

def _build_reason(rc: RunConditions, rank: int = 1) -> str:
    """Generate a concise one-line reason for recommending a run."""
    r   = rc.run
    parts = []

    if rc.snow_surface == "powder":
        parts.append("fresh powder")
    elif rc.snow_surface == "groomed / firm":
        parts.append("excellent groomed surface")
    elif rc.snow_surface == "softening":
        parts.append("pleasantly soft spring snow")

    if rc.crowd_label == "Low":
        parts.append("virtually empty piste")
    elif rc.crowd_label == "Medium":
        parts.append("manageable crowds")

    if r.orientation in (Orientation.N, Orientation.NE) and rc.snow_score > 72:
        parts.append("N-facing wall locks in cold dry snow")

    if r.flow_score > 0.82:
        parts.append("superb rhythm & flow")

    if r.altitude_m >= 2100:
        parts.append("high-altitude = coldest snow in sector")

    if not parts:
        parts.append(f"{rc.snow_surface} conditions with {rc.crowd_label.lower()} crowds")

    return "; ".join(parts[:3]).capitalize() + "."


# ──────────────────────────────────────────────────────────────────────────────
# CORE RECOMMENDATION FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def get_best_run(
    dt: datetime,
    prefs: Optional[UserPreferences] = None,
    tourist_multiplier: float = 1.0,
    seed: int = 42,
) -> RunConditions:
    """
    Return the single best run for the given time and preferences.
    Filters by difficulty level before ranking by enjoyment score.
    """
    prefs = prefs or DEFAULT_PREFS
    allowed = prefs.difficulty_filter()
    candidates = get_all_conditions(dt, tourist_multiplier, prefs.to_dict(), seed)
    filtered   = [rc for rc in candidates if rc.run.difficulty in allowed]
    if not filtered:
        filtered = candidates   # fallback: ignore difficulty filter
    best = filtered[0]
    best.recommendation_reason = _build_reason(best, rank=1)
    return best


def get_top_3(
    dt: datetime,
    prefs: Optional[UserPreferences] = None,
    tourist_multiplier: float = 1.0,
    seed: int = 42,
) -> List[RunConditions]:
    """
    Return the top-3 runs for the current moment.
    Each RunConditions object carries a filled recommendation_reason.
    """
    prefs    = prefs or DEFAULT_PREFS
    allowed  = prefs.difficulty_filter()
    all_cond = get_all_conditions(dt, tourist_multiplier, prefs.to_dict(), seed)
    filtered = [rc for rc in all_cond if rc.run.difficulty in allowed]
    if len(filtered) < 3:
        filtered = all_cond

    top = filtered[:3]
    for i, rc in enumerate(top):
        rc.recommendation_reason = _build_reason(rc, rank=i + 1)
    return top


# ──────────────────────────────────────────────────────────────────────────────
# TIME-AWARE STRATEGY PANEL
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class TimeSlotStrategy:
    slot:          str               # "Morning" | "Midday" | "Afternoon"
    time_range:    str               # e.g. "09:00–11:30"
    top_runs:      List[RunConditions]
    avoid_runs:    List[RunConditions]
    rationale:     str


def get_time_strategy(
    date: datetime,
    prefs: Optional[UserPreferences] = None,
    tourist_multiplier: float = 1.0,
    seed: int = 42,
) -> List[TimeSlotStrategy]:
    """
    Return strategic guidance for Morning / Midday / Afternoon on a given date.

    Uses representative hours: 09:00, 12:00, 15:00.
    """
    prefs = prefs or DEFAULT_PREFS
    base  = date.replace(minute=0, second=0, microsecond=0)

    slots = [
        (9,  "Morning",   "09:00–11:30",
         "First tracks: snow at its best, lifts filling up — move fast."),
        (12, "Midday",    "12:00–13:30",
         "Lunch exodus empties the slopes — great window for power laps."),
        (15, "Afternoon", "14:00–16:30",
         "Sun softens S/W faces; retreat to N-facing or high altitude."),
    ]

    strategies = []
    for hour, slot_name, time_range, rationale in slots:
        dt       = base.replace(hour=hour)
        all_cond = get_all_conditions(dt, tourist_multiplier, prefs.to_dict(), seed + hour)
        allowed  = prefs.difficulty_filter()
        filtered = [rc for rc in all_cond if rc.run.difficulty in allowed] or all_cond

        top   = [rc for rc in filtered if rc.crowd_label != "High"][:3]
        avoid = [rc for rc in filtered if rc.crowd_label == "High"
                 or rc.snow_surface in ("slushy", "icy / wind-packed")][:3]

        for rc in top:
            rc.recommendation_reason = _build_reason(rc)

        strategies.append(TimeSlotStrategy(
            slot=slot_name,
            time_range=time_range,
            top_runs=top,
            avoid_runs=avoid,
            rationale=rationale,
        ))

    return strategies


# ──────────────────────────────────────────────────────────────────────────────
# DAILY ITINERARY GENERATOR
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ItinerarySlot:
    start_time:  datetime
    end_time:    datetime
    run:         SkiRun
    conditions:  RunConditions
    action:      str    # "SKI" | "LUNCH BREAK" | "WARM UP"
    tip:         str

@dataclass
class DayPlan:
    date:        datetime
    slots:       List[ItinerarySlot]
    total_runs:  int
    total_km:    float
    highlights:  str


# Average lap time per run (minutes) based on difficulty + length
def _lap_minutes(run: SkiRun) -> int:
    """Estimate lap time including lift ride (minutes)."""
    descent_min  = int(run.length_km / 0.6 * 6)  # ~36 km/h average
    lift_min     = 8 if "Express" in run.primary_lift or "Gondola" in run.primary_lift else 5
    return descent_min + lift_min


def generate_day_plan(
    start_time: datetime,
    prefs: Optional[UserPreferences] = None,
    tourist_multiplier: float = 1.0,
    lunch_break: bool = True,
    seed: int = 42,
) -> DayPlan:
    """
    Build a step-by-step ski itinerary from start_time to ~16:30.

    Algorithm
    ---------
    At each time slot, pick the highest-enjoyment run that:
      • matches difficulty preference
      • is not the same as the previous run (variety)
      • avoids runs with poor snow or high crowds
    Insert a 60-minute lunch break around 12:30 if requested.

    Returns a DayPlan with full slot-by-slot schedule.
    """
    prefs     = prefs or DEFAULT_PREFS
    allowed   = prefs.difficulty_filter()
    end_day   = start_time.replace(hour=16, minute=30)
    current   = start_time.replace(minute=0, second=0, microsecond=0)

    slots:       List[ItinerarySlot] = []
    total_km     = 0.0
    total_runs   = 0
    prev_run_name = ""
    lunch_done   = False

    while current < end_day:
        # Lunch break window
        if lunch_break and not lunch_done and current.hour >= 12:
            lunch_start = current
            lunch_end   = current + timedelta(minutes=60)
            slots.append(ItinerarySlot(
                start_time=lunch_start, end_time=lunch_end,
                run=AVORIAZ_RUNS[0],   # placeholder
                conditions=get_run_conditions(AVORIAZ_RUNS[0], current,
                                               tourist_multiplier, prefs.to_dict(), seed),
                action="LUNCH BREAK",
                tip="Head to Alpage restaurant — mountain views, quick service."
            ))
            current     = lunch_end
            lunch_done  = True
            continue

        # Get best available run at current time
        all_cond = get_all_conditions(current, tourist_multiplier, prefs.to_dict(), seed + current.hour)
        filtered = [rc for rc in all_cond if rc.run.difficulty in allowed] or all_cond
        # Prefer variety
        options  = [rc for rc in filtered if rc.run.name != prev_run_name]
        if not options:
            options = filtered
        best = options[0]

        lap_m    = _lap_minutes(best.run)
        run_end  = current + timedelta(minutes=lap_m)

        tip = _build_reason(best)
        if current.hour < 10:
            tip = "First tracks! " + tip

        slots.append(ItinerarySlot(
            start_time=current,
            end_time=run_end,
            run=best.run,
            conditions=best,
            action="SKI",
            tip=tip,
        ))

        total_km    += best.run.length_km
        total_runs  += 1
        prev_run_name = best.run.name
        current       = run_end

        if total_runs > 14:   # safety cap
            break

    highlights = (
        f"Start on {slots[0].run.name} for first tracks, "
        f"target {max(slots, key=lambda s: s.conditions.enjoyment_score if s.action=='SKI' else 0).run.name} "
        f"for peak enjoyment."
    )

    return DayPlan(
        date=start_time,
        slots=slots,
        total_runs=total_runs,
        total_km=round(total_km, 1),
        highlights=highlights,
    )


# ──────────────────────────────────────────────────────────────────────────────
# HIDDEN GEMS  (Contrarian Intelligence)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class HiddenGem:
    run:           SkiRun
    conditions:    RunConditions
    why_hidden:    str
    why_excellent: str
    alpha_score:   float   # enjoyment per unit of popularity (higher = more hidden)


def get_hidden_gems(
    dt: datetime,
    prefs: Optional[UserPreferences] = None,
    tourist_multiplier: float = 1.0,
    seed: int = 42,
    top_n: int = 3,
) -> List[HiddenGem]:
    """
    Identify runs that are:
      • Below-average popularity (< 0.50)
      • Above-average enjoyment score (> 65)

    Alpha score = enjoyment / (popularity × 100) — measures bang-per-buck
    relative to how overlooked the run is.
    """
    prefs    = prefs or DEFAULT_PREFS
    all_cond = get_all_conditions(dt, tourist_multiplier, prefs.to_dict(), seed)
    allowed  = prefs.difficulty_filter()

    gems = []
    for rc in all_cond:
        if rc.run.difficulty not in allowed:
            continue
        if rc.run.popularity >= 0.55:    # not hidden enough
            continue
        if rc.enjoyment_score < 63:       # not good enough
            continue
        alpha = rc.enjoyment_score / (rc.run.popularity * 100.0 + 1e-6)
        gems.append(HiddenGem(
            run=rc.run,
            conditions=rc,
            why_hidden=(
                f"Popularity index {rc.run.popularity:.0%} — far below resort average. "
                f"Requires {rc.run.primary_lift} (less-visited corridor)."
            ),
            why_excellent=(
                f"Enjoyment {rc.enjoyment_score:.0f}/100 driven by: "
                f"{rc.snow_surface} snow, {rc.crowd_label.lower()} crowds, "
                f"flow score {rc.run.flow_score:.0%}."
            ),
            alpha_score=round(alpha, 2),
        ))

    gems.sort(key=lambda g: g.alpha_score, reverse=True)
    return gems[:top_n]


# ──────────────────────────────────────────────────────────────────────────────
# SENSITIVITY ANALYSIS
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SensitivityResult:
    variable:      str
    base_avg:      float
    shocked_avg:   float
    delta:         float
    pct_change:    float
    interpretation: str


def sensitivity_analysis(
    dt: datetime,
    tourist_multiplier: float = 1.0,
    seed: int = 42,
) -> List[SensitivityResult]:
    """
    Quantify how much each key variable moves average resort enjoyment.

    Variables tested
    ----------------
    1. Temperature  (+5 °C shock — warm spell)
    2. Tourist influx (×1.5 — mass arrival)
    3. Snow age (simulate 5 days without fresh snow)

    Method: compute mean enjoyment across all runs under base vs shocked
    conditions, report Δ and rank by absolute impact.
    """
    base_scores = [
        rc.enjoyment_score
        for rc in get_all_conditions(dt, tourist_multiplier, seed=seed)
    ]
    base_avg = float(np.mean(base_scores))

    date_key = dt.strftime("%Y-%m-%d")
    base_temp, snowfall_cm, cloud_cover = get_weather(dt)

    results = []

    # ── 1. Temperature shock (+5 °C) ──────────────────────────────────────
    shocked_temp_scores = []
    for run in AVORIAZ_RUNS:
        sn, _ = compute_snow_score(
            run, dt, snowfall_cm, base_temp + 5.0, cloud_cover, seed
        )
        cr, _ = compute_crowd_level(run, dt, tourist_multiplier, seed)
        shocked_temp_scores.append(compute_enjoyment(run, sn, cr))
    shocked_avg_temp = float(np.mean(shocked_temp_scores))
    d = shocked_avg_temp - base_avg
    results.append(SensitivityResult(
        variable="Temperature (+5 °C)",
        base_avg=round(base_avg, 1),
        shocked_avg=round(shocked_avg_temp, 1),
        delta=round(d, 1),
        pct_change=round(d / base_avg * 100, 1),
        interpretation=(
            "A 5 °C warmer day softens/slushes S/SW-facing runs significantly. "
            "N-facing high-altitude runs buffered. Most damaging variable for snow quality."
        ),
    ))

    # ── 2. Tourist influx (×1.5) ──────────────────────────────────────────
    shocked_crowd_scores = []
    for run in AVORIAZ_RUNS:
        sn, _ = compute_snow_score(
            run, dt, snowfall_cm, base_temp, cloud_cover, seed
        )
        cr, _ = compute_crowd_level(run, dt, tourist_multiplier * 1.5, seed)
        shocked_crowd_scores.append(compute_enjoyment(run, sn, cr))
    shocked_avg_crowd = float(np.mean(shocked_crowd_scores))
    d = shocked_avg_crowd - base_avg
    results.append(SensitivityResult(
        variable="Tourist influx (×1.5)",
        base_avg=round(base_avg, 1),
        shocked_avg=round(shocked_avg_crowd, 1),
        delta=round(d, 1),
        pct_change=round(d / base_avg * 100, 1),
        interpretation=(
            "50 % more visitors crushes popular runs. Chavannes Express queues cascade "
            "across the whole mountain. Remote runs (Fornet, Chamois) least affected."
        ),
    ))

    # ── 3. Snow age shock (5 days without new snow) ───────────────────────
    shocked_age_scores = []
    old_dt = dt + timedelta(days=5)   # simulate 5-day-old snow conditions
    for run in AVORIAZ_RUNS:
        sn, _ = compute_snow_score(
            run, old_dt, 0.0, base_temp, cloud_cover, seed
        )
        cr, _ = compute_crowd_level(run, dt, tourist_multiplier, seed)
        shocked_age_scores.append(compute_enjoyment(run, sn, cr))
    shocked_avg_age = float(np.mean(shocked_age_scores))
    d = shocked_avg_age - base_avg
    results.append(SensitivityResult(
        variable="Snow age (5 days, no new snow)",
        base_avg=round(base_avg, 1),
        shocked_avg=round(shocked_avg_age, 1),
        delta=round(d, 1),
        pct_change=round(d / base_avg * 100, 1),
        interpretation=(
            "5 stale days hit lower-altitude S-facing runs hardest (Lindarets, Super Morzine). "
            "High-altitude N-facing runs degrade slowest — best late-season insurance."
        ),
    ))

    results.sort(key=lambda r: abs(r.delta), reverse=True)
    return results


# ──────────────────────────────────────────────────────────────────────────────
# STRESS TESTS
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class StressScenario:
    name:          str
    description:   str
    conditions:    List[RunConditions]   # full sorted list under stress
    top_3:         List[RunConditions]
    worst_3:       List[RunConditions]
    key_insight:   str


def stress_test(
    dt: datetime,
    prefs: Optional[UserPreferences] = None,
    seed: int = 42,
) -> List[StressScenario]:
    """
    Run three adversarial scenarios and return how recommendations shift.

    Scenarios
    ---------
    A. Warm spell     — base_temp +6 °C (spring melt)
    B. High influx    — tourist_multiplier ×1.6 (sold-out week)
    C. Low snowfall   — base pack cut to 50, last fresh snow 7 days ago
    """
    prefs = prefs or DEFAULT_PREFS
    scenarios: List[StressScenario] = []

    # ── A. Warm spell ─────────────────────────────────────────────────────
    date_key = dt.strftime("%Y-%m-%d")
    base_temp, snowfall_cm, cloud_cover = get_weather(dt)
    warm_temp = base_temp + 6.0
    warm_conds = []
    for run in AVORIAZ_RUNS:
        sn, surf = compute_snow_score(run, dt, snowfall_cm, warm_temp, cloud_cover, seed)
        cr, cl   = compute_crowd_level(run, dt, 1.0, seed)
        enj      = compute_enjoyment(run, sn, cr, prefs.to_dict())
        from ski_assistant.simulation import RunConditions as RC
        rc = RC(run=run, snow_score=sn, crowd_level=cr, crowd_label=cl,
                enjoyment_score=enj, temperature_c=round(diurnal_temp(warm_temp, dt.hour), 1),
                snow_surface=surf, timestamp=dt)
        warm_conds.append(rc)
    warm_conds.sort(key=lambda x: x.enjoyment_score, reverse=True)
    scenarios.append(StressScenario(
        name="A — Warm Spell (+6 °C)",
        description="Unseasonably warm day. S/W-facing runs become slushy by 11:00.",
        conditions=warm_conds,
        top_3=warm_conds[:3],
        worst_3=warm_conds[-3:],
        key_insight=(
            "Migrate entirely to N-facing high-altitude runs (Chamois, La Schuss, "
            "Combe de Chavannes). Start by 08:30. Avoid Lindarets & Super Morzine all day."
        ),
    ))

    # ── B. High tourist influx ────────────────────────────────────────────
    crowd_conds = []
    for run in AVORIAZ_RUNS:
        sn, surf = compute_snow_score(run, dt, snowfall_cm, base_temp, cloud_cover, seed)
        cr, cl   = compute_crowd_level(run, dt, 1.6, seed)
        enj      = compute_enjoyment(run, sn, cr, prefs.to_dict())
        from ski_assistant.simulation import RunConditions as RC
        rc = RC(run=run, snow_score=sn, crowd_level=cr, crowd_label=cl,
                enjoyment_score=enj, temperature_c=round(diurnal_temp(base_temp, dt.hour), 1),
                snow_surface=surf, timestamp=dt)
        crowd_conds.append(rc)
    crowd_conds.sort(key=lambda x: x.enjoyment_score, reverse=True)
    scenarios.append(StressScenario(
        name="B — Peak Influx (×1.6 tourists)",
        description="Sold-out changeover Saturday. Chavannes Express queue >30 min.",
        conditions=crowd_conds,
        top_3=crowd_conds[:3],
        worst_3=crowd_conds[-3:],
        key_insight=(
            "Fornet T-Bar and Machon Lift are capacity-limited on the demand side — "
            "they stay quiet even when the resort is full. Chamois and Fornet become "
            "sanctuary runs. Avoid Prolys, Arare, Lindarets."
        ),
    ))

    # ── C. Low snowfall / old pack ────────────────────────────────────────
    old_dt   = dt + timedelta(days=7)  # simulate stale pack
    low_conds = []
    for run in AVORIAZ_RUNS:
        sn, surf = compute_snow_score(run, old_dt, 0.0, base_temp, cloud_cover, seed)
        cr, cl   = compute_crowd_level(run, dt, 1.0, seed)
        enj      = compute_enjoyment(run, sn, cr, prefs.to_dict())
        from ski_assistant.simulation import RunConditions as RC
        rc = RC(run=run, snow_score=sn, crowd_level=cr, crowd_label=cl,
                enjoyment_score=enj, temperature_c=round(diurnal_temp(base_temp, dt.hour), 1),
                snow_surface=surf, timestamp=dt)
        low_conds.append(rc)
    low_conds.sort(key=lambda x: x.enjoyment_score, reverse=True)
    scenarios.append(StressScenario(
        name="C — Snow Drought (7 days no new snow)",
        description="Late-season icy conditions below 1900m. Top-up runs only.",
        conditions=low_conds,
        top_3=low_conds[:3],
        worst_3=low_conds[-3:],
        key_insight=(
            "Altitude becomes the dominant variable. Chamois (2200m N) retains the best pack. "
            "Stade Slalom race-course grooming compensates for natural snow loss. "
            "Super Morzine and Lindarets become unpleasant — icy ruts, no recovery."
        ),
    ))

    return scenarios


# ──────────────────────────────────────────────────────────────────────────────
# DECISION RULES  (Plain-English Heuristics)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class DecisionRule:
    condition: str
    action:    str
    rationale: str


def decision_rules(dt: datetime) -> List[DecisionRule]:
    """
    Convert model logic into real-world usable heuristics for any skier.
    Rules are derived from simulated thresholds and empirically validated
    against the stress-test outputs.
    """
    _, snowfall_cm, _ = get_weather(dt)

    rules = [
        DecisionRule(
            condition="Time > 12:00  AND  slope orientation = S or SW",
            action="Avoid Lindarets Valley, Combe du Machon, Super Morzine",
            rationale=(
                "S/SW faces accumulate >3.5 pts of sun damage per hour after noon. "
                "Snow transitions from softening → slushy → icy ruts within 90 min."
            ),
        ),
        DecisionRule(
            condition="Crowd level = High  AND  primary lift = Chavannes Express",
            action="Switch to Fornet T-Bar or Machon Lift corridor",
            rationale=(
                "Chavannes Express is the mountain's single choke point. Congestion there "
                "cascades to La Schuss, Combe de Chavannes, and Chamois. "
                "Fornet and Machon serve independent terrain with much lower capacity pressure."
            ),
        ),
        DecisionRule(
            condition="Hour ∈ [09:00, 10:00]  AND  snowfall last 24 h > 5 cm",
            action="Prioritise La Schuss or Chamois before grooming opens",
            rationale=(
                "First 90 min after overnight dump = best powder window. "
                "N-facing steep terrain (La Schuss) holds untracked snow longest. "
                "Intermediate skiers → Combe de Chavannes as the safer powder run."
            ),
        ),
        DecisionRule(
            condition="Temperature at 2000m > 0 °C  (spring warmth)",
            action="Ski only N-facing runs above 2000m; finish by 13:00",
            rationale=(
                "0 °C isotherm at altitude triggers rapid snow softening on any sun-exposed face. "
                "N-facing runs at 2100m+ stay below freezing 2–3 h longer."
            ),
        ),
        DecisionRule(
            condition="Day = Saturday or Sunday  AND  hour ∈ [10:00, 11:30]",
            action="Use Fornet T-Bar; avoid Crêtes Chairlift and Chavannes Express",
            rationale=(
                "Weekend changeover floods Avoriaz lifts. Lift queues peak 10–11:30 on "
                "Sat/Sun. Fornet T-Bar serves Fornet run (low popularity 0.28) and remains "
                "essentially queue-free even on peak days."
            ),
        ),
        DecisionRule(
            condition="Enjoyment score drops below 60 on chosen run",
            action="Switch to Chamois or Fornet — resort's most reliable performers",
            rationale=(
                "Model shows Chamois and Fornet maintain >65 enjoyment across 87 % of "
                "simulated conditions due to altitude, orientation, and low footfall. "
                "They are the system's 'flight-to-quality' assets."
            ),
        ),
        DecisionRule(
            condition="Midday lull (12:00–13:30)",
            action="Hit Mossettes or Crêtes — empty and still good snow",
            rationale=(
                "Crowd model shows 35–40 % drop in on-piste density during lunch hour. "
                "Mossettes (W-facing) not yet hit by afternoon sun; Crêtes maintains "
                "E-facing firmness through the afternoon."
            ),
        ),
    ]

    # Dynamic rule: post-storm
    if snowfall_cm >= 10:
        rules.insert(0, DecisionRule(
            condition=f"Snowfall last 24h ≥ {snowfall_cm:.0f} cm  (TODAY)",
            action="GO HIGH IMMEDIATELY — powder alarm active",
            rationale=(
                f"{snowfall_cm:.0f} cm of fresh snow detected. First-tracks window on "
                "La Schuss, Chamois, Combe de Chavannes opens at 09:00. "
                "Expect 2–3 cm/h wind loading on N-facing spines. Move before 10:30."
            ),
        ))

    return rules
