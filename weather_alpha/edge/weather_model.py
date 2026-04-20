"""Forecast -> probability that a threshold is exceeded on a given date.

Strategy: use the ensemble members directly when available (empirical CDF),
otherwise fall back to a Gaussian around the deterministic forecast with a
climatology-derived sigma.
"""

from __future__ import annotations

import math
from statistics import fmean, pstdev

from weather_alpha.data.weather.open_meteo import EnsembleForecast


# Fallback sigma (same units as variable) when we only have a deterministic run.
# Rough order-of-magnitude; better numbers come from the climate-normals module.
FALLBACK_SIGMA = {
    "temp_max_c": 1.5,
    "temp_min_c": 1.5,
    "precip_mm_sum": 4.0,
    "wind_max_kmh": 5.0,
}


def probability_over_threshold(
    forecast: EnsembleForecast,
    *,
    variable: str,
    valid_date: str,
    threshold: float,
    comparator: str = "gte",
    fallback_sigma: float | None = None,
) -> float:
    """Return P(variable {cmp} threshold) on `valid_date`, in [0,1].

    `comparator` is 'gte' (>=) or 'lte' (<=).
    """
    members = [
        t for t in forecast.tracks
        if t.variable == variable and valid_date in t.values
    ]
    if not members:
        return 0.5  # no data -> coin flip; the caller will de-rank by confidence

    values = [t.values[valid_date] for t in members if t.member >= 1]
    if len(values) >= 5:
        if comparator == "lte":
            hits = sum(1 for v in values if v <= threshold)
        else:
            hits = sum(1 for v in values if v >= threshold)
        return _clamp(hits / len(values))

    # Fall back to Gaussian around the deterministic run.
    det = next((t for t in members if t.member == 0), members[0])
    mu = det.values[valid_date]
    if values:
        sigma = pstdev(values) or (fallback_sigma or FALLBACK_SIGMA.get(variable, 1.0))
        mu = fmean(values + [mu])
    else:
        sigma = fallback_sigma or FALLBACK_SIGMA.get(variable, 1.0)

    z = (threshold - mu) / max(sigma, 1e-6)
    cdf = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    if comparator == "lte":
        return _clamp(cdf)
    return _clamp(1.0 - cdf)


def _clamp(p: float) -> float:
    return max(0.0, min(1.0, p))
