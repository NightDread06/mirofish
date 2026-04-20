"""Time hedge: same question, different resolution date (today vs tomorrow)."""

from __future__ import annotations

from weather_alpha.storage.dao import Market


def time_hedge(primary: Market, candidates: list[Market]) -> Market | None:
    same = [
        c for c in candidates
        if c.id != primary.id
        and c.city == primary.city
        and c.threshold_type == primary.threshold_type
        and c.threshold_value == primary.threshold_value
        and c.comparator == primary.comparator
        and c.resolves_at != primary.resolves_at
    ]
    if not same:
        return None
    # Prefer the nearest-dated alternative.
    same.sort(key=lambda c: (c.resolves_at or "~"))
    return same[0]
