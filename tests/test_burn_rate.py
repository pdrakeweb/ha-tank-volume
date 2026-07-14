"""Tests for the burn-rate calculator."""

from custom_components.tank_volume.burn_rate import BurnRateCalculator

DAY = 86400.0


def _feed(calc, start_gal, rate_per_day, days, step_hours=1, t0=0.0):
    """Feed a steady decline of rate_per_day gal/day, returning the last timestamp."""
    n = int(days * 24 / step_hours)
    t = t0
    for i in range(n + 1):
        t = t0 + i * step_hours * 3600.0
        calc.add(t, start_gal - rate_per_day * (t - t0) / DAY)
    return t


def test_empty_returns_none():
    assert BurnRateCalculator(window_seconds=7 * DAY).daily_burn(0.0) is None


def test_steady_consumption():
    calc = BurnRateCalculator(window_seconds=7 * DAY)
    t = _feed(calc, 300.0, 2.0, days=10)
    assert abs(calc.daily_burn(t) - 2.0) < 0.05


def test_flat_tank_is_zero():
    calc = BurnRateCalculator(window_seconds=7 * DAY)
    t = _feed(calc, 250.0, 0.0, days=10)
    assert calc.daily_burn(t) == 0.0


def test_refill_only_is_clamped_to_zero():
    """A pure increase (net fill) must not read as negative burn."""
    calc = BurnRateCalculator(window_seconds=7 * DAY)
    t = _feed(calc, 200.0, -1.0, days=10)  # volume rising 1 gal/day
    assert calc.daily_burn(t) == 0.0


def test_refill_mid_window_ignored():
    calc = BurnRateCalculator(window_seconds=7 * DAY, refill_threshold=30.0)
    # 5 days consuming 2/day, then a +150 refill, then 5 more days consuming 2/day.
    t = _feed(calc, 300.0, 2.0, days=5)
    base = 300.0 - 2.0 * 5
    t = _feed(calc, base + 150.0, 2.0, days=5, t0=t + 3600.0)
    assert abs(calc.daily_burn(t) - 2.0) < 0.15


def test_insufficient_span_returns_none():
    """Only a little data (less than half the window span) -> no estimate yet."""
    calc = BurnRateCalculator(window_seconds=7 * DAY, min_span_fraction=0.5)
    t = _feed(calc, 300.0, 2.0, days=1)  # only 1 day < 3.5-day min span
    assert calc.daily_burn(t) is None


def test_recent_refill_returns_none():
    """Just after a refill there isn't enough post-refill data to estimate."""
    calc = BurnRateCalculator(window_seconds=7 * DAY, refill_threshold=30.0)
    t = _feed(calc, 300.0, 2.0, days=6)
    calc.add(t + 3600.0, 400.0)  # refill just now
    calc.add(t + 7200.0, 399.9)
    assert calc.daily_burn(t + 7200.0) is None


def test_out_of_order_ignored():
    calc = BurnRateCalculator(window_seconds=7 * DAY)
    calc.add(1000.0, 100.0)
    calc.add(500.0, 999.0)  # older than last -> ignored
    assert calc.has_samples
    # Not enough span for an estimate, but the stale point must not corrupt state.
    assert calc.daily_burn(1000.0) is None


def test_window_prunes_old_samples():
    calc = BurnRateCalculator(window_seconds=2 * DAY, history_margin_seconds=3600.0)
    _feed(calc, 300.0, 2.0, days=10)
    # Buffer should be bounded to ~window + margin, not all 10 days.
    assert calc.coverage_seconds <= 2 * DAY + 3600.0 + 3600.0
