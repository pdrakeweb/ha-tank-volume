"""Bulk (lagged) temperature estimation for tank volume temperature compensation.

The liquid in a tank does not track the measured temperature instantaneously. On a
Mopeka-style sensor magnetically clamped to the *outside* of the tank bottom, the
reported temperature follows the tank skin / ambient, which changes faster than the
bulk propane because of the liquid's thermal mass. The reported temperature therefore
*leads* the volume response by several hours, and compensating volumetric expansion
against the instantaneous reading corrects at the wrong phase.

Empirically (a full year of tank data, 4-84 F) that lead is strongly and consistently
**temperature dependent** -- roughly ``lag_hours = 1.1 + 0.067 * T_degF`` (about 2-3 h
in cold weather, 6-7 h when warm) -- and effectively independent of how full the tank
is. This module reconstructs an estimate of the bulk temperature by looking back a
temperature-dependent transport delay (plus a small averaging window) over the history
of measured temperatures. The delay is selected from a slow (seasonal) temperature so
it does not wobble with the daily cycle.

The class is deliberately free of any Home Assistant imports so the algorithm can be
unit-tested in isolation. Temperatures are unit-agnostic numbers; the caller feeds a
consistent unit (the sensor platform normalises to Fahrenheit, which the default lag
slope/reference assume).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class _Sample:
    """A single timestamped temperature reading (epoch seconds, value)."""

    t: float
    value: float


class BulkTemperatureEstimator:
    """Estimate delayed/low-passed bulk temperature from a stream of readings.

    Args:
        lag_seconds: Transport delay at ``reference_temperature``. ``0`` with a zero
            slope reproduces the legacy behaviour of using the latest reading.
        smoothing_seconds: Width of the averaging window centred on the delayed target
            time, used to denoise the delayed reading. ``0`` uses linear interpolation.
        lag_slope_seconds_per_degree: How much the delay grows per degree of (seasonal)
            temperature above ``reference_temperature``. ``0`` gives a constant delay.
        reference_temperature: Temperature at which the delay equals ``lag_seconds``.
        min_lag_seconds / max_lag_seconds: Bounds applied to the temperature-dependent
            delay (ignored when the slope is zero).
        season_time_constant_seconds: Time constant of the slow temperature average used
            to pick the delay, so the delay tracks the season rather than the daily cycle.
        history_margin_seconds: Extra history retained beyond what the lag/smoothing
            require, so short sensor gaps don't starve the estimator.
    """

    def __init__(
        self,
        lag_seconds: float,
        smoothing_seconds: float = 0.0,
        lag_slope_seconds_per_degree: float = 0.0,
        reference_temperature: float = 60.0,
        min_lag_seconds: float = 3600.0,
        max_lag_seconds: float = 43200.0,
        season_time_constant_seconds: float = 86400.0,
        history_margin_seconds: float = 3600.0,
    ) -> None:
        """Initialize the estimator."""
        self._lag0 = max(0.0, lag_seconds)
        self._smoothing = max(0.0, smoothing_seconds)
        self._lag_slope = lag_slope_seconds_per_degree
        self._ref = reference_temperature
        self._min_lag = max(0.0, min_lag_seconds)
        self._max_lag = max(self._min_lag, max_lag_seconds)
        self._season_tau = max(1.0, season_time_constant_seconds)
        self._margin = max(0.0, history_margin_seconds)
        self._samples: deque[_Sample] = deque()
        self._season_temp: float | None = None
        self._season_t: float | None = None

    @property
    def has_samples(self) -> bool:
        """Whether any readings have been recorded."""
        return bool(self._samples)

    @property
    def season_temperature(self) -> float | None:
        """Slow (seasonal) temperature average used to pick the delay."""
        return self._season_temp

    @property
    def coverage_seconds(self) -> float:
        """Span of retained history (newest minus oldest sample time)."""
        if len(self._samples) < 2:
            return 0.0
        return self._samples[-1].t - self._samples[0].t

    def current_lag_seconds(self) -> float:
        """The transport delay currently in effect, given the seasonal temperature."""
        if self._lag_slope == 0.0:
            return self._lag0
        season = self._season_temp
        if season is None:
            season = self._samples[-1].value if self._samples else self._ref
        lag = self._lag0 + self._lag_slope * (season - self._ref)
        return max(self._min_lag, min(self._max_lag, lag))

    def _effective_max_lag(self) -> float:
        return self._lag0 if self._lag_slope == 0.0 else self._max_lag

    def add(self, timestamp: float, value: float) -> None:
        """Record a temperature reading. Out-of-order readings are ignored."""
        if self._samples and timestamp <= self._samples[-1].t:
            return
        self._samples.append(_Sample(timestamp, value))
        # Update the slow (seasonal) temperature as an exponential moving average.
        if self._season_temp is None or self._season_t is None:
            self._season_temp = value
        else:
            dt = timestamp - self._season_t
            if dt > 0:
                alpha = 1.0 - math.exp(-dt / self._season_tau)
                self._season_temp += alpha * (value - self._season_temp)
        self._season_t = timestamp
        self._prune(timestamp)

    def _prune(self, now: float) -> None:
        horizon = now - (self._effective_max_lag() + self._smoothing / 2.0 + self._margin)
        while len(self._samples) > 1 and self._samples[0].t < horizon:
            self._samples.popleft()

    def estimate(self, now: float) -> float | None:
        """Return the estimated bulk temperature at ``now``.

        Returns ``None`` only when no readings are available. During the initial warm-up
        (before a full delay of history has accumulated) the oldest available reading is
        used, so the effective delay grows gracefully toward the configured value.
        """
        if not self._samples:
            return None

        target = now - self.current_lag_seconds()

        if target >= self._samples[-1].t:
            return self._samples[-1].value
        if target <= self._samples[0].t:
            return self._samples[0].value

        if self._smoothing > 0.0:
            half = self._smoothing / 2.0
            window = [s.value for s in self._samples if target - half <= s.t <= target + half]
            if window:
                return sum(window) / len(window)

        return self._interpolate(target)

    def _interpolate(self, target: float) -> float:
        prev = self._samples[0]
        for sample in self._samples:
            if sample.t >= target:
                span = sample.t - prev.t
                if span <= 0:
                    return sample.value
                frac = (target - prev.t) / span
                return prev.value + frac * (sample.value - prev.value)
            prev = sample
        return self._samples[-1].value
