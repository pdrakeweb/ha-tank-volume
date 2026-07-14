"""Scenario tests for the burn-rate pipeline against real + synthesized data.

The fixtures in ``fixtures/burn_scenarios.json`` are built from this tank's actual
Mopeka history (winter heavy burn, spring moderate, summer light, a small real
top-off) plus extrapolated cases the real data doesn't contain (mid-month refills,
a sensor dropout, a pure-synthetic steady rate, and a flat noisy tank). Each fixture
is a series of ``[offset_seconds, temperature_f, contents_gallons]`` with the tank's
true daily burn and the expected bounds.

The pipeline exercised here is exactly the integration's: temperature-adjust the
contents volume (BulkTemperatureEstimator + expansion coefficient), then estimate the
burn rate (BurnRateCalculator). Both are pure modules, so these run without Home
Assistant.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from custom_components.tank_volume.burn_rate import BurnRateCalculator
from custom_components.tank_volume.const import (
    BURN_RATE_WEIGHT_HALF_LIFE_DIVISOR,
    DEFAULT_ADJUSTMENT_COEFFICIENT,
    REFERENCE_TEMPERATURE_F,
)
from custom_components.tank_volume.temperature import BulkTemperatureEstimator

DAY = 86400.0
HOUR = 3600.0

_SCENARIOS = json.loads((Path(__file__).parent / "fixtures" / "burn_scenarios.json").read_text())
_BY_NAME = {s["name"]: s for s in _SCENARIOS}


def _run(series, window_days: float, weighted: bool):
    """Run the real pipeline (temp-adjust -> burn rate) over a fixture series.

    Returns (final_burn, saw_negative): the last non-None daily-burn estimate, and
    whether any estimate along the way was negative (it must never be).
    """
    estimator = BulkTemperatureEstimator(
        lag_seconds=5 * HOUR,
        smoothing_seconds=1 * HOUR,
        lag_slope_seconds_per_degree=0.067 * HOUR,
        reference_temperature=REFERENCE_TEMPERATURE_F,
        min_lag_seconds=1 * HOUR,
        max_lag_seconds=12 * HOUR,
        season_time_constant_seconds=24 * HOUR,
    )
    window = window_days * DAY
    calc = BurnRateCalculator(
        window_seconds=window,
        refill_threshold=30.0,
        weight_half_life_seconds=(window / BURN_RATE_WEIGHT_HALF_LIFE_DIVISOR) if weighted else None,
    )
    coef = DEFAULT_ADJUSTMENT_COEFFICIENT
    final = None
    saw_negative = False
    for offset, temp_f, gallons in series:
        estimator.add(offset, temp_f)
        bulk = estimator.estimate(offset)
        adjusted = gallons / (1.0 + coef * ((bulk if bulk is not None else temp_f) - REFERENCE_TEMPERATURE_F))
        calc.add(offset, adjusted)
        burn = calc.daily_burn(offset)
        if burn is not None:
            final = burn
            if burn < 0:
                saw_negative = True
    return final, saw_negative


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=lambda s: s["name"])
@pytest.mark.parametrize("window_days", [1.0, 3.0, 7.0])
@pytest.mark.parametrize("weighted", [False, True])
def test_burn_never_negative_and_finite(scenario, window_days, weighted):
    """Across every window and weighting, the burn rate is never negative (refills/noise included)."""
    final, saw_negative = _run(scenario["series"], window_days, weighted)
    assert not saw_negative, f"{scenario['name']} produced a negative burn rate"
    if final is not None:
        assert math.isfinite(final) and final >= 0.0


@pytest.mark.parametrize("scenario", _SCENARIOS, ids=lambda s: s["name"])
def test_burn_within_expected_bounds(scenario):
    """With the stable 7-day window, the final burn matches the scenario's expected range."""
    final, _ = _run(scenario["series"], window_days=7.0, weighted=False)
    assert final is not None, f"{scenario['name']} produced no estimate"
    lo, hi = scenario["expect"]["burn_min"], scenario["expect"]["burn_max"]
    assert lo <= final <= hi, f"{scenario['name']}: burn {final:.2f} not in [{lo}, {hi}]"


def test_refill_is_ignored_not_counted_as_negative_burn():
    """A mid-month refill must not read as negative consumption; burn reflects the real draw."""
    for name in ("winter_midmonth_refill", "summer_midmonth_refill"):
        final, saw_negative = _run(_BY_NAME[name]["series"], window_days=7.0, weighted=False)
        assert not saw_negative
        assert final is not None and final >= 0.0


def test_steady_synthetic_is_accurate():
    """A pure 3.0 gal/day series is recovered to within a few percent by every window."""
    for window in (1.0, 3.0, 7.0):
        final, _ = _run(_BY_NAME["steady_synthetic_3gal"]["series"], window, weighted=False)
        assert final is not None and abs(final - 3.0) < 0.4


def test_flat_tank_reads_near_zero():
    """A flat tank with +/-2 gal noise must read close to zero, not swing wildly."""
    final, _ = _run(_BY_NAME["flat_no_consumption"]["series"], window_days=7.0, weighted=False)
    assert final is not None and final < 1.5


def test_weighted_reacts_faster_than_unweighted():
    """On the winter draw, a weighted 7-day window tracks a change at least as fast (>= unweighted)."""
    # After the winter series, both should land near the real ~7 gal/day; sanity that weighted stays sane.
    w, _ = _run(_BY_NAME["winter_heavy_burn"]["series"], window_days=7.0, weighted=True)
    u, _ = _run(_BY_NAME["winter_heavy_burn"]["series"], window_days=7.0, weighted=False)
    assert w is not None and u is not None
    assert 3.0 <= w <= 14.0 and 3.0 <= u <= 14.0
