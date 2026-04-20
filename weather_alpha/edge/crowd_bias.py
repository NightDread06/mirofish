"""Detect retail overreaction from recent snapshots.

Heuristic: if the YES mid has moved more than N standard deviations in the last
hour with rising volume, the crowd is chasing. Return a SIGNED additive
correction to the model probability (positive means the model is still higher
than market => crowd pushed price down too much => fade the panic up).
"""

from __future__ import annotations

from statistics import fmean, pstdev

from weather_alpha.storage.dao import Snapshot


def crowd_overreaction_score(recent: list[Snapshot]) -> float:
    """Returns an additive correction in [-0.10, +0.10]."""
    mids = [s.yes_mid for s in recent if s.yes_mid is not None]
    if len(mids) < 10:
        return 0.0

    long_mean = fmean(mids)
    long_std = pstdev(mids) or 1e-6
    last = mids[-1]
    z = (last - long_mean) / long_std

    # Panic down: z<-2 => fade up ~+0.04. Euphoria up: z>2 => fade down ~-0.04.
    if z <= -2.0:
        return min(0.10, 0.02 * abs(z))
    if z >= 2.0:
        return max(-0.10, -0.02 * z)
    return 0.0
