"""APScheduler loop: ticks the engine and hands results to the dashboard."""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from weather_alpha.api import create_app, record_tick_result
from weather_alpha.config import get_settings
from weather_alpha.engine import run_tick

log = logging.getLogger("weather_alpha.scheduler")


async def _tick(execute: bool) -> None:
    try:
        result = await run_tick(execute=execute)
        record_tick_result(result)
        log.info(
            "tick: %d opportunities, %d orders", len(result.opportunities), len(result.orders_placed)
        )
    except Exception:
        log.exception("tick failed")


def build_scheduler(*, execute: bool = True) -> AsyncIOScheduler:
    s = get_settings()
    sched = AsyncIOScheduler()
    sched.add_job(
        lambda: asyncio.create_task(_tick(execute=execute)),
        "interval",
        seconds=s.edge_tick_interval_s,
        id="edge-tick",
        next_run_time=None,
    )
    return sched


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    import uvicorn

    app = create_app()
    sched = build_scheduler(execute=True)

    @app.on_event("startup")
    async def _startup() -> None:
        sched.start()
        await _tick(execute=False)  # warm up dashboard

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        sched.shutdown(wait=False)

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
