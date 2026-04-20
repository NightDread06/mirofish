"""City x threshold_type x lead_time mispricing factor.

Until we have resolved markets in our DB, this returns neutral (0.0).
Kept as its own function so the full pipeline wires in cleanly now.
"""

from __future__ import annotations


def city_threshold_bias(
    *,
    city: str | None,
    threshold_type: str | None,
    lead_time_hours: float,
) -> float:
    """Additive correction, e.g. +0.05 means historically YES was 5pp under-priced."""
    # Placeholder. Once `resolutions` table has >= ~30 rows we replace this with:
    #   SELECT AVG((resolved_yes - closing_yes)) FROM resolutions JOIN markets ...
    return 0.0
