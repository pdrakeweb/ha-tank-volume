"""Burn-rate estimation for tank contents.

Estimates the average daily consumption (gallons/day) from a history of the
(temperature-adjusted) contents volume, using a least-squares trend over a
multi-day window rather than a noisy endpoint difference.

Why a multi-day trend: over a short window (e.g. 72 h) the real consumption can
be smaller than the sensor noise, so an endpoint difference swings wildly and,
extrapolated to a month, explodes. A regression slope over ~7 days averages the
noise down and rejects the (roughly zero-mean over 24 h) daily thermal wave,
giving a stable rate. Refills are detected as a large upward jump and the trend
is measured only over the data since the most recent refill.

The class is free of Home Assistant imports so the algorithm can be unit-tested
in isolation. It works in whatever volume unit it is fed (the sensor platform
feeds gallons) and epoch-second timestamps.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

SECONDS_PER_DAY = 86400.0


@dataclass(frozen=True)
class _Sample:
    t: float
    value: float


class BurnRateCalculator:
    """Estimate average daily consumption from a contents-volume history.

    Args:
        window_seconds: Length of the trailing window the trend is fitted over.
        refill_threshold: An increase larger than this between consecutive samples
            is treated as a refill; the trend is fitted only on samples after it.
        min_samples: Minimum samples required in the (post-refill) window.
        min_span_fraction: The fitted samples must span at least this fraction of
            ``window_seconds`` (or one day, whichever is smaller) for a valid
            estimate; otherwise ``None`` is returned (e.g. just after a refill).
        history_margin_seconds: Extra history retained beyond the window.
    """

    def __init__(
        self,
        window_seconds: float,
        refill_threshold: float = 30.0,
        min_samples: int = 6,
        min_span_fraction: float = 0.5,
        weight_half_life_seconds: float | None = None,
        history_margin_seconds: float = 3600.0,
    ) -> None:
        """Initialize the calculator.

        When ``weight_half_life_seconds`` is set, the trend is a *weighted* least-squares
        fit whose weights halve every ``weight_half_life_seconds`` back from ``now`` — so
        recent readings dominate and the estimate reacts faster to a change in usage while
        still averaging over the whole window. ``None`` uses a uniform (unweighted) fit.
        """
        self._window = max(1.0, window_seconds)
        self._refill = refill_threshold
        self._min_samples = max(2, min_samples)
        self._min_span = min_span_fraction * self._window
        self._half_life = weight_half_life_seconds if (weight_half_life_seconds or 0) > 0 else None
        self._margin = max(0.0, history_margin_seconds)
        self._samples: deque[_Sample] = deque()

    @property
    def has_samples(self) -> bool:
        """Whether any readings have been recorded."""
        return bool(self._samples)

    @property
    def coverage_seconds(self) -> float:
        """Span of retained history (newest minus oldest sample time)."""
        if len(self._samples) < 2:
            return 0.0
        return self._samples[-1].t - self._samples[0].t

    @property
    def retention_seconds(self) -> float:
        """How far back readings are retained/used (window plus margin)."""
        return self._window + self._margin

    def add(self, timestamp: float, value: float) -> None:
        """Record a contents-volume reading. Out-of-order readings are ignored."""
        if self._samples and timestamp <= self._samples[-1].t:
            return
        self._samples.append(_Sample(timestamp, value))
        horizon = timestamp - (self._window + self._margin)
        while len(self._samples) > 1 and self._samples[0].t < horizon:
            self._samples.popleft()

    def daily_burn(self, now: float) -> float | None:
        """Return the estimated consumption in units/day (>= 0), or None.

        None means there isn't enough usable history yet (cold start, or just
        after a refill) — callers should hold the previous value, or fall back
        to :meth:`daily_burn_provisional`, rather than emitting a value they
        don't trust.
        """
        return self._estimate(now, self._min_samples, self._min_span)

    def daily_burn_provisional(self, now: float) -> float | None:
        """Best-effort estimate from whatever little history exists, or None.

        Deliberately loose: it needs only two readings spanning any positive
        time, so a brand-new sensor produces a (possibly wildly inaccurate)
        number immediately instead of sitting at ``unknown``. The estimate
        self-corrects as the window fills and :meth:`daily_burn` takes over.
        Returns None only when a rate genuinely can't be formed yet (fewer than
        two readings, or no time elapsed between them).
        """
        return self._estimate(now, 2, 0.0)

    def _estimate(self, now: float, min_samples: int, min_span: float) -> float | None:
        """Fit the (optionally weighted) trend under the given sample/span gates."""
        window = [s for s in self._samples if s.t >= now - self._window]
        if len(window) < min_samples:
            return None

        # Restart the trend after the most recent refill (large upward step).
        start = 0
        for i in range(1, len(window)):
            if window[i].value - window[i - 1].value > self._refill:
                start = i
        seg = window[start:]
        if len(seg) < min_samples:
            return None

        span = seg[-1].t - seg[0].t
        if span <= 0 or span < min_span:
            return None

        weights = None
        if self._half_life is not None:
            weights = [0.5 ** ((now - s.t) / self._half_life) for s in seg]
        slope = _ols_slope(seg, weights)  # units per second (negative while consuming)
        if slope is None:
            return None
        return max(0.0, -slope * SECONDS_PER_DAY)


def _ols_slope(samples: list[_Sample], weights: list[float] | None = None) -> float | None:
    """(Optionally weighted) least-squares slope (value per second) of value vs time."""
    n = len(samples)
    t0 = samples[0].t
    xs = [s.t - t0 for s in samples]
    ys = [s.value for s in samples]
    if weights is None:
        weights = [1.0] * n
    sw = sum(weights)
    if sw <= 0:
        return None
    mx = sum(weights[i] * xs[i] for i in range(n)) / sw
    my = sum(weights[i] * ys[i] for i in range(n)) / sw
    den = sum(weights[i] * (xs[i] - mx) ** 2 for i in range(n))
    if den == 0:
        return None
    return sum(weights[i] * (xs[i] - mx) * (ys[i] - my) for i in range(n)) / den
