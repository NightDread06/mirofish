"""
Avoriaz Ski Visualization Layer
=================================
Text-based dashboard (terminal) + matplotlib plots.

Functions
---------
  print_dashboard(dt, prefs)           → rich terminal dashboard
  plot_crowd_heatmap(date)             → crowd density across runs × hours
  plot_snow_evolution(date)            → snow quality decay through the day
  plot_enjoyment_comparison(dt, prefs) → side-by-side run scores
  plot_stress_comparison(dt)           → base vs stress-test scenarios
  print_sensitivity_report(results)    → formatted sensitivity table
  print_strategy_panel(strategies)     → time-slot strategy cards
  print_itinerary(plan)                → formatted day plan
  print_hidden_gems(gems)              → contrarian intelligence cards
  print_decision_rules(rules)          → heuristic rule sheet
"""

from __future__ import annotations

import os
import sys
import textwrap
from datetime import datetime, timedelta
from typing import List, Optional

import numpy as np

# ── graceful matplotlib backend (headless-safe) ───────────────────────────────
import matplotlib
matplotlib.use("Agg")   # non-interactive; saves to file
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import FancyBboxPatch

from ski_assistant.simulation import (
    AVORIAZ_RUNS,
    Difficulty,
    Orientation,
    RunConditions,
    build_daily_series,
    get_all_conditions,
    get_weather,
)
from ski_assistant.decision_engine import (
    DayPlan,
    DecisionRule,
    HiddenGem,
    SensitivityResult,
    StressScenario,
    TimeSlotStrategy,
    UserPreferences,
    get_top_3,
    get_hidden_gems,
    sensitivity_analysis,
    stress_test,
    get_time_strategy,
    DEFAULT_PREFS,
)

# ──────────────────────────────────────────────────────────────────────────────
# TERMINAL COLOUR HELPERS
# ──────────────────────────────────────────────────────────────────────────────

_USE_COLOUR = sys.stdout.isatty() or os.environ.get("FORCE_COLOUR")

def _c(text: str, code: str) -> str:
    """Wrap text in ANSI colour code (no-op if not tty)."""
    if not _USE_COLOUR:
        return text
    return f"\033[{code}m{text}\033[0m"

def green(t):  return _c(t, "92")
def cyan(t):   return _c(t, "96")
def yellow(t): return _c(t, "93")
def red(t):    return _c(t, "91")
def bold(t):   return _c(t, "1")
def dim(t):    return _c(t, "2")
def blue(t):   return _c(t, "94")
def magenta(t):return _c(t, "95")

def crowd_colour(label: str) -> str:
    mapping = {"Low": green, "Medium": yellow, "High": red}
    fn = mapping.get(label, lambda x: x)
    return fn(label)

def snow_colour(score: float) -> str:
    if score >= 75: return green(f"{score:.0f}")
    elif score >= 55: return yellow(f"{score:.0f}")
    else: return red(f"{score:.0f}")

def enj_colour(score: float) -> str:
    if score >= 72: return green(f"{score:.0f}")
    elif score >= 58: return yellow(f"{score:.0f}")
    else: return red(f"{score:.0f}")

DIFF_SYMBOL = {
    Difficulty.GREEN: green("●"),
    Difficulty.BLUE:  blue("●"),
    Difficulty.RED:   red("●"),
    Difficulty.BLACK: bold("◆"),
}

def divider(char: str = "─", width: int = 72) -> str:
    return dim(char * width)


# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD  (Terminal)
# ──────────────────────────────────────────────────────────────────────────────

def print_dashboard(
    dt: datetime,
    prefs: Optional[UserPreferences] = None,
    tourist_multiplier: float = 1.0,
    seed: int = 42,
) -> None:
    """Full terminal dashboard — call this to see where to ski RIGHT NOW."""
    prefs = prefs or DEFAULT_PREFS
    _, snowfall_cm, cloud_cover = get_weather(dt)

    print()
    print(bold("╔══════════════════════════════════════════════════════════════════════╗"))
    print(bold("║") + cyan("   ⛷  AVORIAZ SKI ASSISTANT  —  LIVE DECISION ENGINE              ") + bold("║"))
    print(bold("╚══════════════════════════════════════════════════════════════════════╝"))
    print(f"  {dim('📅')} {bold(dt.strftime('%A %d %B %Y'))}   "
          f"{dim('🕐')} {bold(dt.strftime('%H:%M'))}   "
          f"{dim('❄')}  Snowfall 24h: {bold(f'{snowfall_cm:.0f} cm')}   "
          f"{dim('☁')}  Cloud: {bold(f'{cloud_cover*100:.0f}%')}")
    print()

    # ── TOP 3 ──────────────────────────────────────────────────────────────
    top3 = get_top_3(dt, prefs, tourist_multiplier, seed)

    print(bold("┌─  🟢  TOP 3 RUNS RIGHT NOW  ───────────────────────────────────────┐"))
    print()

    medals = ["🥇", "🥈", "🥉"]
    for i, rc in enumerate(top3):
        r = rc.run
        diff_sym = DIFF_SYMBOL.get(r.difficulty, "●")
        print(f"  {medals[i]}  {bold(r.name.upper())}  {diff_sym}  {dim(r.difficulty.value.capitalize())}  "
              f"— {dim(r.length_km)} km @ {dim(str(r.altitude_m)+'m')}")
        print(f"     Snow  : {snow_colour(rc.snow_score)}/100  [{rc.snow_surface}]")
        print(f"     Crowd : {crowd_colour(rc.crowd_label)}  ({rc.crowd_level:.0%} occupied)")
        print(f"     Enjoy : {enj_colour(rc.enjoyment_score)}/100")
        print(f"     📍  {dim(rc.recommendation_reason)}")
        if i < 2:
            print(f"  {divider('┄', 66)}")
    print()
    print(bold("└────────────────────────────────────────────────────────────────────┘"))
    print()


# ──────────────────────────────────────────────────────────────────────────────
# STRATEGY PANEL  (Terminal)
# ──────────────────────────────────────────────────────────────────────────────

def print_strategy_panel(
    strategies: List[TimeSlotStrategy],
    show_avoid: bool = True,
) -> None:
    """Print the time-aware strategy panel."""
    print(bold("┌─  📅  TIME-AWARE STRATEGY PANEL  ──────────────────────────────────┐"))
    print()

    slot_icons = {"Morning": "🌅", "Midday": "☀️ ", "Afternoon": "🌇"}

    for s in strategies:
        icon = slot_icons.get(s.slot, "🕐")
        print(f"  {icon}  {bold(s.slot.upper())}  {dim(s.time_range)}")
        print(f"     {dim(s.rationale)}")
        print()

        if s.top_runs:
            print(f"     {green('✓ GO:')}  ", end="")
            run_names = [f"{bold(rc.run.name)} ({enj_colour(rc.enjoyment_score)})" for rc in s.top_runs]
            print("  /  ".join(run_names))

        if show_avoid and s.avoid_runs:
            print(f"     {red('✗ AVOID:')} ", end="")
            avoid_names = [bold(rc.run.name) for rc in s.avoid_runs]
            print("  /  ".join(avoid_names))

        print()
        print(f"  {divider('─', 66)}")

    print(bold("└────────────────────────────────────────────────────────────────────┘"))
    print()


# ──────────────────────────────────────────────────────────────────────────────
# ITINERARY  (Terminal)
# ──────────────────────────────────────────────────────────────────────────────

def print_itinerary(plan: DayPlan) -> None:
    """Print the step-by-step day plan."""
    print(bold("┌─  🎯  DAY PLAN  ────────────────────────────────────────────────────┐"))
    print(f"  {dim('Date:')} {bold(plan.date.strftime('%A %d %B'))}   "
          f"{dim('Runs:')} {bold(str(plan.total_runs))}   "
          f"{dim('Distance:')} {bold(str(plan.total_km) + ' km')}")
    print(f"  {dim('Highlight:')} {plan.highlights}")
    print()

    for slot in plan.slots:
        t_start = slot.start_time.strftime("%H:%M")
        t_end   = slot.end_time.strftime("%H:%M")
        if slot.action == "LUNCH BREAK":
            print(f"  {yellow('🍽')}  {bold(t_start)} → {t_end}  {yellow('LUNCH BREAK')}")
            print(f"       {dim(slot.tip)}")
        elif slot.action == "SKI":
            diff = slot.run.difficulty
            sym  = DIFF_SYMBOL.get(diff, "●")
            enj  = slot.conditions.enjoyment_score
            print(f"  {sym}  {bold(t_start)} → {t_end}  {bold(slot.run.name)}"
                  f"  {dim('—')} {enj_colour(enj)}/100  [{slot.conditions.snow_surface}]")
            print(f"       {dim(slot.tip)}")
        print()

    print(bold("└────────────────────────────────────────────────────────────────────┘"))
    print()


# ──────────────────────────────────────────────────────────────────────────────
# HIDDEN GEMS  (Terminal)
# ──────────────────────────────────────────────────────────────────────────────

def print_hidden_gems(gems: List[HiddenGem]) -> None:
    """Print contrarian intelligence panel."""
    print(bold("┌─  💎  HIDDEN GEMS  —  CONTRARIAN INTELLIGENCE  ───────────────────┐"))
    print()
    print(f"  {dim('Runs with high enjoyment + low popularity = model alpha signal')}")
    print()

    for i, gem in enumerate(gems):
        rc = gem.conditions
        diff_sym = DIFF_SYMBOL.get(gem.run.difficulty, "●")
        print(f"  #{i+1}  {bold(gem.run.name.upper())}  {diff_sym}  "
              f"Enjoy: {enj_colour(rc.enjoyment_score)}/100  "
              f"α-score: {bold(f'{gem.alpha_score:.1f}')}")
        print(f"     {dim('Why hidden:')}    {gem.why_hidden}")
        print(f"     {dim('Why excellent:')} {gem.why_excellent}")
        if i < len(gems) - 1:
            print(f"  {divider('┄', 66)}")

    print()
    print(bold("└────────────────────────────────────────────────────────────────────┘"))
    print()


# ──────────────────────────────────────────────────────────────────────────────
# SENSITIVITY REPORT  (Terminal)
# ──────────────────────────────────────────────────────────────────────────────

def print_sensitivity_report(results: List[SensitivityResult]) -> None:
    """Print sensitivity analysis table."""
    print(bold("┌─  📊  SENSITIVITY ANALYSIS  ───────────────────────────────────────┐"))
    print()
    print(f"  {'Variable':<35} {'Base':>6} {'Shocked':>8} {'Δ':>6} {'%':>7}")
    print(f"  {divider('─', 63)}")
    for i, r in enumerate(results):
        rank = f"#{i+1}"
        delta_str = (red if r.delta < 0 else green)(f"{r.delta:+.1f}")
        pct_str   = (red if r.pct_change < 0 else green)(f"{r.pct_change:+.1f}%")
        print(f"  {bold(rank)} {r.variable:<33} {r.base_avg:>6.1f} {r.shocked_avg:>8.1f}"
              f"  {delta_str:>10}  {pct_str:>10}")
        print(f"     {dim(textwrap.shorten(r.interpretation, 64))}")
        print()

    print(bold("└────────────────────────────────────────────────────────────────────┘"))
    print()


# ──────────────────────────────────────────────────────────────────────────────
# STRESS TEST  (Terminal)
# ──────────────────────────────────────────────────────────────────────────────

def print_stress_tests(scenarios: List[StressScenario]) -> None:
    """Print stress-test scenario summary."""
    print(bold("┌─  ⚠️   STRESS TESTS  ────────────────────────────────────────────────┐"))
    print()
    for s in scenarios:
        print(f"  {bold(s.name)}")
        print(f"  {dim(s.description)}")
        print()

        top_names  = " / ".join(bold(rc.run.name) for rc in s.top_3)
        worst_names= " / ".join(rc.run.name for rc in s.worst_3)
        print(f"     {green('→ BEST:')}  {top_names}")
        print(f"     {red('→ AVOID:')} {worst_names}")
        print(f"     {dim('Insight:')} {s.key_insight}")
        print()
        print(f"  {divider('─', 66)}")

    print(bold("└────────────────────────────────────────────────────────────────────┘"))
    print()


# ──────────────────────────────────────────────────────────────────────────────
# DECISION RULES  (Terminal)
# ──────────────────────────────────────────────────────────────────────────────

def print_decision_rules(rules: List[DecisionRule]) -> None:
    """Print plain-English decision rule sheet."""
    print(bold("┌─  📋  DECISION RULES  —  FIELD-READY HEURISTICS  ─────────────────┐"))
    print()
    for i, rule in enumerate(rules):
        print(f"  {bold(f'Rule {i+1}')}")
        print(f"  {cyan('IF')}    {rule.condition}")
        print(f"  {green('THEN')}  {bold(rule.action)}")
        print(f"  {dim('WHY')}   {textwrap.fill(rule.rationale, 64, subsequent_indent=' ' * 8)}")
        print()

    print(bold("└────────────────────────────────────────────────────────────────────┘"))
    print()


# ──────────────────────────────────────────────────────────────────────────────
# MATPLOTLIB PLOTS
# ──────────────────────────────────────────────────────────────────────────────

_PALETTE = {
    "N":  "#2196F3",  "NE": "#4CAF50",  "E":  "#8BC34A",
    "SE": "#FFEB3B", "S":  "#FF5722",  "SW": "#FF9800",
    "W":  "#F44336",  "NW": "#9C27B0",
}

_DIFF_COLOURS = {
    Difficulty.GREEN: "#4CAF50",
    Difficulty.BLUE:  "#2196F3",
    Difficulty.RED:   "#F44336",
    Difficulty.BLACK: "#212121",
}


def plot_crowd_heatmap(
    date: datetime,
    tourist_multiplier: float = 1.0,
    save_path: str = "crowd_heatmap.png",
    seed: int = 42,
) -> str:
    """
    Crowd density heatmap: runs × hours.
    Saves PNG and returns file path.
    """
    hours = list(range(8, 17))
    run_names = [r.name for r in AVORIAZ_RUNS]
    series = build_daily_series(date, hours, tourist_multiplier, seed)

    data = np.zeros((len(AVORIAZ_RUNS), len(hours)))
    for j, h in enumerate(hours):
        cond_map = {rc.run.name: rc.crowd_level for rc in series[h]}
        for i, run in enumerate(AVORIAZ_RUNS):
            data[i, j] = cond_map.get(run.name, 0)

    fig, ax = plt.subplots(figsize=(13, 7))
    cmap = plt.cm.RdYlGn_r
    im = ax.imshow(data, cmap=cmap, vmin=0, vmax=1, aspect="auto", interpolation="bilinear")

    # Labels
    ax.set_xticks(range(len(hours)))
    ax.set_xticklabels([f"{h:02d}:00" for h in hours], fontsize=9)
    ax.set_yticks(range(len(AVORIAZ_RUNS)))
    ax.set_yticklabels(
        [f"{r.name}  ({r.difficulty.value[0].upper()})" for r in AVORIAZ_RUNS],
        fontsize=9,
    )

    # Annotate cells
    for i in range(len(AVORIAZ_RUNS)):
        for j in range(len(hours)):
            val = data[i, j]
            label = "L" if val < 0.35 else ("M" if val < 0.62 else "H")
            ax.text(j, i, label, ha="center", va="center",
                    fontsize=7, color="white" if val > 0.55 else "black",
                    fontweight="bold")

    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Crowd Level  (0 = empty  →  1 = packed)", fontsize=9)

    ax.set_title(
        f"⛷  Avoriaz Crowd Density Heatmap  —  {date.strftime('%A %d %B %Y')}",
        fontsize=13, fontweight="bold", pad=14,
    )
    ax.set_xlabel("Hour of Day", fontsize=10)
    ax.set_ylabel("Run", fontsize=10)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    return save_path


def plot_snow_evolution(
    date: datetime,
    save_path: str = "snow_evolution.png",
    seed: int = 42,
) -> str:
    """
    Snow quality evolution through the day per run.
    Lines coloured by orientation to show sun-exposure decay.
    """
    hours  = list(range(8, 17))
    series = build_daily_series(date, hours, 1.0, seed)

    fig, ax = plt.subplots(figsize=(13, 6))

    for run in AVORIAZ_RUNS:
        scores = [
            next(rc.snow_score for rc in series[h] if rc.run.name == run.name)
            for h in hours
        ]
        colour = _PALETTE.get(run.orientation.value, "#999")
        lw     = 2.2 if run.orientation in (Orientation.N, Orientation.NE) else 1.4
        ls     = "-" if run.difficulty in (Difficulty.RED, Difficulty.BLACK) else "--"
        ax.plot(hours, scores, color=colour, lw=lw, ls=ls,
                label=f"{run.name} ({run.orientation.value})", alpha=0.85)

    ax.axhline(70, color="#888", lw=0.8, ls=":")
    ax.text(16.9, 70.5, "Good  ↑", fontsize=7, color="#888", ha="right")
    ax.axhline(55, color="#e88", lw=0.8, ls=":")
    ax.text(16.9, 55.5, "Marginal  ↑", fontsize=7, color="#e88", ha="right")

    ax.set_xlim(8, 16)
    ax.set_ylim(20, 100)
    ax.set_xticks(hours)
    ax.set_xticklabels([f"{h:02d}:00" for h in hours], fontsize=9)
    ax.set_xlabel("Hour of Day", fontsize=10)
    ax.set_ylabel("Snow Quality Score (0–100)", fontsize=10)
    ax.set_title(
        f"❄  Snow Quality Evolution  —  {date.strftime('%A %d %B %Y')}",
        fontsize=13, fontweight="bold", pad=14,
    )
    ax.legend(loc="lower left", fontsize=7, ncol=3, framealpha=0.7)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    return save_path


def plot_enjoyment_comparison(
    dt: datetime,
    prefs: Optional[UserPreferences] = None,
    tourist_multiplier: float = 1.0,
    save_path: str = "enjoyment_comparison.png",
    seed: int = 42,
) -> str:
    """
    Horizontal bar chart of enjoyment scores for all runs.
    Bars coloured by difficulty. Snow score and crowd shown as secondary.
    """
    prefs    = prefs or DEFAULT_PREFS
    all_cond = get_all_conditions(dt, tourist_multiplier, prefs.to_dict(), seed)
    all_cond.reverse()   # ascending so highest is at top

    names  = [rc.run.name for rc in all_cond]
    enj    = [rc.enjoyment_score for rc in all_cond]
    snow   = [rc.snow_score for rc in all_cond]
    crowd  = [(1 - rc.crowd_level) * 100 for rc in all_cond]
    colours= [_DIFF_COLOURS[rc.run.difficulty] for rc in all_cond]

    fig, axes = plt.subplots(1, 3, figsize=(16, 7), sharey=True)
    fig.suptitle(
        f"⛷  Run Comparison  —  {dt.strftime('%A %d %B  %H:%M')}",
        fontsize=13, fontweight="bold",
    )

    datasets = [
        (axes[0], enj,   "Enjoyment Score",  colours, 0, 100),
        (axes[1], snow,  "Snow Quality",      "#2196F3", 0, 100),
        (axes[2], crowd, "Crowd Freedom (100 = empty)", "#4CAF50", 0, 100),
    ]

    for ax, vals, title, col, vmin, vmax in datasets:
        bars = ax.barh(names, vals, color=col, edgecolor="white", linewidth=0.5, height=0.65)
        for bar, v in zip(bars, vals):
            ax.text(v + 1, bar.get_y() + bar.get_height() / 2,
                    f"{v:.0f}", va="center", fontsize=8)
        ax.set_xlim(vmin, vmax + 10)
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.axvline(70, color="#aaa", lw=0.8, ls=":")
        ax.set_xlabel("Score", fontsize=9)
        ax.tick_params(labelsize=8)

    # Legend for difficulty
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c, label=d.value.capitalize())
                       for d, c in _DIFF_COLOURS.items()]
    axes[0].legend(handles=legend_elements, loc="lower right", fontsize=7, framealpha=0.7)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    return save_path


def plot_stress_comparison(
    dt: datetime,
    prefs: Optional[UserPreferences] = None,
    save_path: str = "stress_comparison.png",
    seed: int = 42,
) -> str:
    """
    Grouped bar chart comparing average enjoyment score across:
      base conditions vs three stress scenarios.
    Per-run breakdown shows which runs are resilient vs fragile.
    """
    prefs    = prefs or DEFAULT_PREFS
    base_all = get_all_conditions(dt, 1.0, prefs.to_dict(), seed)
    scenarios = stress_test(dt, prefs, seed)

    run_names = [rc.run.name for rc in base_all]
    base_enj  = {rc.run.name: rc.enjoyment_score for rc in base_all}

    scenario_enj = []
    for sc in scenarios:
        enj_map = {rc.run.name: rc.enjoyment_score for rc in sc.conditions}
        scenario_enj.append(enj_map)

    x     = np.arange(len(run_names))
    width = 0.18
    fig, ax = plt.subplots(figsize=(16, 6))

    bar_sets = [
        ("Base", [base_enj.get(n, 0) for n in run_names], "#2196F3"),
        (scenarios[0].name.split("—")[1].strip(), [scenario_enj[0].get(n, 0) for n in run_names], "#FF9800"),
        (scenarios[1].name.split("—")[1].strip(), [scenario_enj[1].get(n, 0) for n in run_names], "#F44336"),
        (scenarios[2].name.split("—")[1].strip(), [scenario_enj[2].get(n, 0) for n in run_names], "#9C27B0"),
    ]

    for i, (label, vals, colour) in enumerate(bar_sets):
        offset = (i - 1.5) * width
        ax.bar(x + offset, vals, width, label=label, color=colour, alpha=0.82, edgecolor="white", lw=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(run_names, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Enjoyment Score (0–100)", fontsize=10)
    ax.set_title("⚠  Stress Test: Enjoyment Score by Run × Scenario", fontsize=13, fontweight="bold")
    ax.axhline(65, color="#888", lw=0.8, ls=":", label="Quality threshold")
    ax.set_ylim(0, 105)
    ax.legend(fontsize=8, loc="upper right")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    return save_path


def plot_weekly_outlook(
    save_path: str = "weekly_outlook.png",
    seed: int = 42,
) -> str:
    """
    Weekly overview: best run enjoyment score for each day (10:00 reference hour).
    Shows snow and crowd separately as stacked components.
    """
    from ski_assistant.simulation import DAILY_WEATHER, compute_snow_score, compute_crowd_level, compute_enjoyment

    dates = sorted(DAILY_WEATHER.keys())
    labels = []
    best_enj, best_snow, best_crowd_free = [], [], []

    for d in dates:
        dt = datetime.strptime(d + " 10:00", "%Y-%m-%d %H:%M")
        all_cond = get_all_conditions(dt, 1.0, seed=seed)
        best = all_cond[0]
        labels.append(dt.strftime("%a\n%d %b"))
        best_enj.append(best.enjoyment_score)
        best_snow.append(best.snow_score)
        best_crowd_free.append((1 - best.crowd_level) * 100)

    x = np.arange(len(dates))
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    axes[0].bar(x, best_enj, color="#2196F3", alpha=0.85, label="Best run enjoyment")
    axes[0].axhline(70, color="#aaa", lw=0.8, ls=":")
    axes[0].set_ylabel("Enjoyment Score", fontsize=10)
    axes[0].set_title("📅  Weekly Outlook — Best Achievable Enjoyment (@ 10:00)", fontsize=12, fontweight="bold")
    axes[0].legend(fontsize=9)
    axes[0].set_ylim(0, 105)
    for xi, v in enumerate(best_enj):
        axes[0].text(xi, v + 1, f"{v:.0f}", ha="center", fontsize=9, fontweight="bold")

    # Snow quality vs crowd freedom
    w = 0.35
    axes[1].bar(x - w/2, best_snow, w, label="Snow quality", color="#4DD0E1", alpha=0.85)
    axes[1].bar(x + w/2, best_crowd_free, w, label="Crowd freedom", color="#A5D6A7", alpha=0.85)
    axes[1].axhline(70, color="#aaa", lw=0.8, ls=":")
    axes[1].set_ylabel("Score (0–100)", fontsize=10)
    axes[1].set_xlabel("Date", fontsize=10)
    axes[1].legend(fontsize=9)
    axes[1].set_ylim(0, 110)

    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, fontsize=9)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    return save_path


# ──────────────────────────────────────────────────────────────────────────────
# COMBINED SAVE-ALL HELPER
# ──────────────────────────────────────────────────────────────────────────────

def save_all_plots(
    dt: datetime,
    prefs: Optional[UserPreferences] = None,
    output_dir: str = ".",
    seed: int = 42,
) -> List[str]:
    """Generate and save all charts; returns list of file paths."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    paths = [
        plot_crowd_heatmap(dt,  save_path=os.path.join(output_dir, "crowd_heatmap.png"), seed=seed),
        plot_snow_evolution(dt, save_path=os.path.join(output_dir, "snow_evolution.png"), seed=seed),
        plot_enjoyment_comparison(dt, prefs, save_path=os.path.join(output_dir, "enjoyment_comparison.png"), seed=seed),
        plot_stress_comparison(dt, prefs,    save_path=os.path.join(output_dir, "stress_comparison.png"), seed=seed),
        plot_weekly_outlook(                 save_path=os.path.join(output_dir, "weekly_outlook.png"), seed=seed),
    ]
    return paths
