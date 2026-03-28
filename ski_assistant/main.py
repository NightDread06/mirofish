"""
Avoriaz Ski Assistant  —  Live Decision Engine
================================================
Entry point for the full app-style dashboard.

Usage
-----
  # Live mode (uses current system time):
  python -m ski_assistant.main

  # Specific time:
  python -m ski_assistant.main --time "2026-04-01 10:30"

  # With preferences:
  python -m ski_assistant.main --time "2026-03-29 09:00" \\
         --difficulty intermediate \\
         --prioritize-snow 0.8 \\
         --avoid-crowds 0.7 \\
         --no-plots

  # Itinerary only:
  python -m ski_assistant.main --itinerary

  # Save plots to directory:
  python -m ski_assistant.main --plots-dir ./charts
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

# ── ensure package root is on path when run as script ─────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ski_assistant.decision_engine import (
    UserPreferences,
    decision_rules,
    generate_day_plan,
    get_hidden_gems,
    get_time_strategy,
    get_top_3,
    sensitivity_analysis,
    stress_test,
)
from ski_assistant.visualization import (
    bold, cyan, green, yellow, red, dim, divider,
    print_dashboard,
    print_decision_rules,
    print_hidden_gems,
    print_itinerary,
    print_sensitivity_report,
    print_strategy_panel,
    print_stress_tests,
    save_all_plots,
)

SEASON_START = datetime(2026, 3, 28)
SEASON_END   = datetime(2026, 4,  4, 17, 0)


# ──────────────────────────────────────────────────────────────────────────────
# HEADER / FOOTER
# ──────────────────────────────────────────────────────────────────────────────

def _print_header(dt: datetime, prefs: UserPreferences) -> None:
    print()
    print(bold("═" * 72))
    print(bold(" ⛷  AVORIAZ SKI ASSISTANT  v1.0  —  Portes du Soleil"))
    print(bold("═" * 72))
    print(f"  {dim('Powered by Mirofish Decision Engine  |  Season ends 04 Apr 2026')}")
    print()
    print(f"  {cyan('Query time')}      : {bold(dt.strftime('%A %d %B %Y  %H:%M'))}")
    print(f"  {cyan('Difficulty')}      : {bold(prefs.difficulty_level.capitalize())}")
    print(f"  {cyan('Snow priority')}   : {bold(f'{prefs.prioritize_snow:.0%}')}")
    print(f"  {cyan('Crowd avoidance')} : {bold(f'{prefs.avoid_crowds:.0%}')}")
    print()

def _print_footer(plot_paths: list | None) -> None:
    print(bold("═" * 72))
    print(bold("  🏔  END OF REPORT  |  Avoriaz Ski Assistant"))
    if plot_paths:
        print()
        print(f"  {green('Charts saved:')}")
        for p in plot_paths:
            print(f"    • {p}")
    print(bold("═" * 72))
    print()


# ──────────────────────────────────────────────────────────────────────────────
# SECTION PRINTERS (wrap each panel with a header line)
# ──────────────────────────────────────────────────────────────────────────────

def section(title: str) -> None:
    print()
    print(bold(f"## {title}"))
    print(divider())


# ──────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ──────────────────────────────────────────────────────────────────────────────

def run_app(
    dt: datetime,
    prefs: UserPreferences,
    tourist_multiplier: float = 1.0,
    plots_dir: str | None = None,
    itinerary_only: bool = False,
    seed: int = 42,
) -> None:
    """
    Full app-style output:

      1.  Live Dashboard      — Top 3 runs RIGHT NOW
      2.  Time Strategy       — Morning / Midday / Afternoon breakdown
      3.  Day Itinerary       — Step-by-step plan
      4.  Hidden Gems         — Contrarian intelligence
      5.  Sensitivity Analysis
      6.  Stress Tests
      7.  Decision Rules
      8.  Charts (optional)
    """
    _print_header(dt, prefs)

    # ── guard: season check ────────────────────────────────────────────────
    if dt > SEASON_END:
        print(red("  ⚠  Season has ended (04 Apr 2026). Data shown for last valid day."))
        dt = SEASON_END.replace(hour=10)
    elif dt < SEASON_START:
        print(yellow("  ⚠  Date is before tracked season start. Using 28 Mar 2026."))
        dt = SEASON_START.replace(hour=10)

    if itinerary_only:
        section("🎯  DAILY ITINERARY")
        plan = generate_day_plan(dt, prefs, tourist_multiplier, seed=seed)
        print_itinerary(plan)
        _print_footer(None)
        return

    # ── 1. Live Dashboard ──────────────────────────────────────────────────
    section("🟢  LIVE RECOMMENDATIONS  —  WHERE TO SKI RIGHT NOW")
    print_dashboard(dt, prefs, tourist_multiplier, seed)

    # ── 2. Time Strategy ───────────────────────────────────────────────────
    section("📅  TIME-AWARE STRATEGY  —  FULL DAY BREAKDOWN")
    strategies = get_time_strategy(dt, prefs, tourist_multiplier, seed)
    print_strategy_panel(strategies)

    # ── 3. Itinerary ───────────────────────────────────────────────────────
    section("🎯  DAILY ITINERARY  —  HOUR-BY-HOUR PLAN")
    plan = generate_day_plan(dt, prefs, tourist_multiplier, seed=seed)
    print_itinerary(plan)

    # ── 4. Hidden Gems ─────────────────────────────────────────────────────
    section("💎  HIDDEN GEMS  —  CONTRARIAN INTELLIGENCE")
    gems = get_hidden_gems(dt, prefs, tourist_multiplier, seed)
    if gems:
        print_hidden_gems(gems)
    else:
        print(f"  {dim('No hidden gems found for current preferences — broaden difficulty to find them.')}")
        print()

    # ── 5. Sensitivity Analysis ────────────────────────────────────────────
    section("📊  MODEL INSIGHTS  —  SENSITIVITY ANALYSIS")
    sens = sensitivity_analysis(dt, tourist_multiplier, seed)
    print_sensitivity_report(sens)

    # ── 6. Stress Tests ────────────────────────────────────────────────────
    section("⚠   STRESS TESTS  —  HOW RECOMMENDATIONS SHIFT")
    scenarios = stress_test(dt, prefs, seed)
    print_stress_tests(scenarios)

    # ── 7. Decision Rules ──────────────────────────────────────────────────
    section("📋  STRATEGY  —  FIELD-READY DECISION RULES")
    rules = decision_rules(dt)
    print_decision_rules(rules)

    # ── 8. Charts ──────────────────────────────────────────────────────────
    plot_paths = None
    if plots_dir is not None:
        section("📈  GENERATING CHARTS")
        print(f"  Saving to: {bold(plots_dir)}")
        print()
        plot_paths = save_all_plots(dt, prefs, plots_dir, seed)
        for p in plot_paths:
            print(f"  {green('✓')} {p}")
        print()

    _print_footer(plot_paths)


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Avoriaz Ski Assistant — Live Decision Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--time", "-t",
        default=None,
        help='Query datetime. Format: "YYYY-MM-DD HH:MM". Defaults to now (clamped to season).',
    )
    p.add_argument(
        "--difficulty", "-d",
        choices=["beginner", "intermediate", "advanced", "all"],
        default="all",
        help="Difficulty level filter (default: all).",
    )
    p.add_argument(
        "--prioritize-snow", "-s",
        type=float, default=0.5,
        metavar="0-1",
        help="Weight for snow quality in enjoyment score (default: 0.5).",
    )
    p.add_argument(
        "--avoid-crowds", "-c",
        type=float, default=0.5,
        metavar="0-1",
        help="Weight for crowd avoidance in enjoyment score (default: 0.5).",
    )
    p.add_argument(
        "--tourists", "-T",
        type=float, default=1.0,
        metavar="0.5-2.0",
        help="Tourist influx multiplier — 1.0 = normal, 1.5 = busy, 0.7 = quiet (default: 1.0).",
    )
    p.add_argument(
        "--itinerary", "-i",
        action="store_true",
        help="Print day itinerary only (fast mode).",
    )
    p.add_argument(
        "--plots-dir", "-p",
        default=None,
        metavar="DIR",
        help="Directory to save matplotlib charts. Omit to skip chart generation.",
    )
    p.add_argument(
        "--seed",
        type=int, default=42,
        help="Random seed for reproducible simulation (default: 42).",
    )
    return p.parse_args()


def _resolve_time(time_arg: str | None) -> datetime:
    """Parse --time arg or use current time, clamped to season."""
    if time_arg:
        try:
            return datetime.strptime(time_arg, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                return datetime.strptime(time_arg, "%Y-%m-%d")
            except ValueError:
                print(red(f"  ⚠  Cannot parse time '{time_arg}'. Using now."))

    now = datetime.now()
    # Clamp to season range for demo purposes
    if now < SEASON_START or now > SEASON_END:
        return datetime(2026, 3, 28, 10, 0)
    return now


def main() -> None:
    args = _parse_args()
    dt   = _resolve_time(args.time)
    prefs = UserPreferences(
        prioritize_snow  = max(0.0, min(1.0, args.prioritize_snow)),
        avoid_crowds     = max(0.0, min(1.0, args.avoid_crowds)),
        difficulty_level = args.difficulty,
    )
    run_app(
        dt               = dt,
        prefs            = prefs,
        tourist_multiplier = args.tourists,
        plots_dir        = args.plots_dir,
        itinerary_only   = args.itinerary,
        seed             = args.seed,
    )


if __name__ == "__main__":
    main()
