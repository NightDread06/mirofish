"""weather-alpha CLI.

Commands:
  scan           Run one tick, print ranked opportunity cards.
  trade          Run one tick AND place paper/live orders.
  paper-pnl      Show open paper positions + rolling PnL.
  positions      List all current positions (paper + live).
  init-db        (Re)create SQLite schema at the configured path.
  reset-kill     Clear the kill-switch flag after manual review.
  serve          Launch the FastAPI dashboard (port 8000).
"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from weather_alpha.config import get_settings
from weather_alpha.engine import run_tick
from weather_alpha.reports.opportunity_card import render_card
from weather_alpha.storage import dao, init_db, get_engine


app = typer.Typer(add_completion=False, help="Polymarket weather alpha engine.")
console = Console()


@app.command()
def scan(top: int = typer.Option(10, help="Print top-N opportunities")) -> None:
    """Fetch markets + forecasts, print opportunity cards."""
    result = asyncio.run(run_tick(execute=False))
    if not result.opportunities:
        console.print("[yellow]No active weather markets with tradeable books.[/yellow]")
        return
    for o in result.opportunities[:top]:
        console.rule(o.question[:80])
        size_pct = 0.0
        console.print(render_card(o, size_pct_bankroll=size_pct))


@app.command()
def trade(top: int = typer.Option(5, help="Consider top-N for execution")) -> None:
    """Run a tick and actually place orders (paper by default)."""
    result = asyncio.run(run_tick(execute=True))
    console.print(f"[green]{len(result.orders_placed)} orders placed[/green]")
    for o in result.orders_placed:
        console.print(o)


@app.command("paper-pnl")
def paper_pnl() -> None:
    """Show open paper positions and realized PnL today."""
    positions = dao.open_paper_positions()
    realized = dao.daily_realized_pnl()
    bankroll = get_settings().bankroll_usd

    t = Table(title="Open paper positions")
    t.add_column("market_id")
    t.add_column("side")
    t.add_column("size_usd", justify="right")
    t.add_column("avg_price", justify="right")
    t.add_column("opened_at")
    for p in positions:
        t.add_row(
            p["market_id"][:14],
            p["side"],
            f"{p['size_usd']:.2f}",
            f"{p['avg_price']:.3f}",
            p["opened_at"][:19],
        )
    console.print(t)
    console.print(f"Bankroll: ${bankroll:.2f}  |  Realized PnL today: ${realized:+.2f}")


@app.command()
def positions() -> None:
    """Alias for paper-pnl."""
    paper_pnl()


@app.command("init-db")
def init_db_cmd() -> None:
    init_db(get_engine())
    console.print(f"[green]DB initialized at {get_settings().db_path}[/green]")


@app.command("reset-kill")
def reset_kill() -> None:
    dao.reset_kill_switch()
    console.print("[green]Kill switch cleared.[/green]")


@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Launch the FastAPI dashboard (portfolio / history / balance)."""
    import uvicorn
    from weather_alpha.api import create_app

    uvicorn.run(create_app(), host=host, port=port, log_level="info")


if __name__ == "__main__":
    app()
