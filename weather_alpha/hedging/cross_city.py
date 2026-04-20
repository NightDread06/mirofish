"""Cross-city hedge: a geographically close city on the same threshold_type."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from weather_alpha.storage.dao import Market


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(radians, a)
    lat2, lon2 = map(radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def cross_city_hedge(
    primary: Market, candidates: list[Market], *, max_km: float = 600.0
) -> Market | None:
    if primary.lat is None or primary.lon is None:
        return None
    target_threshold = primary.threshold_type
    nearby = [
        c for c in candidates
        if c.id != primary.id
        and c.threshold_type == target_threshold
        and c.lat is not None and c.lon is not None
        and _haversine_km((primary.lat, primary.lon), (c.lat, c.lon)) <= max_km
    ]
    if not nearby:
        return None
    return min(
        nearby,
        key=lambda c: _haversine_km((primary.lat, primary.lon), (c.lat, c.lon)),
    )
