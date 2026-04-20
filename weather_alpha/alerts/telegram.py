"""Telegram push notifications (best-effort, never raises)."""

from __future__ import annotations

import asyncio

import httpx

from weather_alpha.config import get_settings


async def _send(text: str) -> None:
    s = get_settings()
    if not s.telegram_bot_token or not s.telegram_chat_id:
        return
    url = f"https://api.telegram.org/bot{s.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(url, data={"chat_id": s.telegram_chat_id, "text": text})
        except Exception:
            pass


def push(text: str) -> None:
    """Fire-and-forget; callers never await."""
    try:
        asyncio.get_event_loop().create_task(_send(text))
    except RuntimeError:
        # Not in an event loop — run a one-shot.
        asyncio.run(_send(text))
