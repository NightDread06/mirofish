"""Cross-threshold hedge: buy >35C / sell >37C, same city + date."""

from __future__ import annotations

from weather_alpha.storage.dao import Market


def cross_threshold_hedge(primary: Market, candidates: list[Market]) -> Market | None:
    if primary.threshold_type is None or primary.threshold_value is None:
        return None
    tier = 2.0 if primary.threshold_type.startswith("temp") else 0.2 * primary.threshold_value

    def same_market(c: Market) -> bool:
        return (
            c.id != primary.id
            and c.city == primary.city
            and c.threshold_type == primary.threshold_type
            and c.comparator == primary.comparator
            and c.resolves_at == primary.resolves_at
        )

    close = [c for c in candidates if same_market(c)]
    # Pick the next-more-extreme threshold in the same direction.
    if primary.comparator == "gte":
        step = [c for c in close if (c.threshold_value or 0) > primary.threshold_value]
        return min(step, key=lambda c: c.threshold_value) if step else None
    else:
        step = [c for c in close if (c.threshold_value or 0) < primary.threshold_value]
        return max(step, key=lambda c: c.threshold_value) if step else None
