"""Tests for the bulk temperature (transport-lag) estimator."""

from custom_components.tank_volume.temperature import BulkTemperatureEstimator


def test_empty_returns_none():
    """No readings -> no estimate."""
    assert BulkTemperatureEstimator(lag_seconds=3600).estimate(0.0) is None


def test_zero_lag_uses_latest():
    """Lag 0 reproduces the legacy behaviour of using the newest reading."""
    est = BulkTemperatureEstimator(lag_seconds=0.0)
    est.add(0.0, 10.0)
    est.add(600.0, 20.0)
    assert est.estimate(600.0) == 20.0


def test_delay_reads_from_the_past():
    """With a 1 h lag the estimate reflects the reading ~1 h earlier."""
    est = BulkTemperatureEstimator(lag_seconds=3600.0)
    # Linear ramp: value equals minutes/10 sampled every 10 minutes for ~3 h.
    for i in range(20):
        est.add(i * 600.0, float(i))
    # now = 19*600 s; target = now - 3600 s -> 6 samples earlier -> value ~ 13.
    assert abs(est.estimate(19 * 600.0) - 13.0) < 0.5


def test_cold_start_uses_oldest():
    """Before a full lag of history exists, fall back to the oldest reading."""
    est = BulkTemperatureEstimator(lag_seconds=36000.0)
    est.add(0.0, 50.0)
    est.add(600.0, 51.0)
    assert est.estimate(1200.0) == 50.0


def test_out_of_order_ignored():
    """Readings older than the newest are ignored to keep the buffer sorted."""
    est = BulkTemperatureEstimator(lag_seconds=0.0)
    est.add(1000.0, 5.0)
    est.add(500.0, 99.0)
    assert est.estimate(1000.0) == 5.0


def test_smoothing_averages_window():
    """A smoothing window averages readings centred on the delayed target time."""
    est = BulkTemperatureEstimator(lag_seconds=600.0, smoothing_seconds=1200.0)
    for i in range(10):
        est.add(i * 300.0, float(i * 2))  # 0, 2, 4, ... every 5 min
    now = 9 * 300.0  # 2700 s
    # Target = now - 600 = 2100 s; window +/-600 s -> t = 1500,1800,2100,2400,2700
    # -> values 10,12,14,16,18 -> mean 14.
    assert est.estimate(now) == 14.0


def test_interpolation_between_samples():
    """Without smoothing the delayed value is linearly interpolated."""
    est = BulkTemperatureEstimator(lag_seconds=100.0)
    est.add(0.0, 0.0)
    est.add(200.0, 20.0)
    # now=200 -> target=100 -> halfway -> 10.0
    assert est.estimate(200.0) == 10.0


def test_pruning_bounds_history():
    """Old samples beyond lag + smoothing + margin are pruned."""
    est = BulkTemperatureEstimator(lag_seconds=3600.0, smoothing_seconds=0.0, history_margin_seconds=600.0)
    for i in range(600):
        est.add(i * 60.0, float(i))  # every minute for 10 h
    # Horizon = last_t - (3600 + 0 + 600) = last_t - 4200 s. Only ~70 samples kept.
    assert est.coverage_seconds <= 3600.0 + 600.0 + 120.0
    assert est.has_samples


def test_negative_parameters_clamped():
    """Negative lag/smoothing are treated as zero."""
    est = BulkTemperatureEstimator(lag_seconds=-5.0, smoothing_seconds=-5.0)
    assert est.current_lag_seconds() == 0.0
    est.add(0.0, 42.0)
    assert est.estimate(0.0) == 42.0


def test_constant_lag_when_slope_zero():
    """With zero slope the lag is exactly lag_seconds regardless of temperature."""
    est = BulkTemperatureEstimator(lag_seconds=4 * 3600.0, lag_slope_seconds_per_degree=0.0)
    for i in range(30):
        est.add(i * 3600.0, 20.0 + i)  # rising temperature
    assert est.current_lag_seconds() == 4 * 3600.0


def test_lag_grows_with_temperature():
    """A positive slope makes the delay longer in warm weather than cold."""
    slope = 0.067 * 3600.0  # seconds of lag per degree F
    cold = BulkTemperatureEstimator(
        lag_seconds=5 * 3600.0,
        lag_slope_seconds_per_degree=slope,
        reference_temperature=60.0,
        season_time_constant_seconds=1.0,  # near-instant season tracking for the test
    )
    warm = BulkTemperatureEstimator(
        lag_seconds=5 * 3600.0,
        lag_slope_seconds_per_degree=slope,
        reference_temperature=60.0,
        season_time_constant_seconds=1.0,
    )
    for i in range(48):
        cold.add(i * 3600.0, 25.0)
        warm.add(i * 3600.0, 80.0)
    cold_lag = cold.current_lag_seconds() / 3600.0
    warm_lag = warm.current_lag_seconds() / 3600.0
    # ~ 5 + 0.067*(25-60) = 2.7 h  vs  5 + 0.067*(80-60) = 6.3 h
    assert 2.0 < cold_lag < 3.5
    assert 6.0 < warm_lag < 7.0
    assert warm_lag > cold_lag + 2.0


def test_lag_is_clamped():
    """The temperature-dependent lag stays within the configured bounds."""
    est = BulkTemperatureEstimator(
        lag_seconds=5 * 3600.0,
        lag_slope_seconds_per_degree=0.067 * 3600.0,
        reference_temperature=60.0,
        min_lag_seconds=1 * 3600.0,
        max_lag_seconds=8 * 3600.0,
        season_time_constant_seconds=1.0,
    )
    for i in range(48):
        est.add(i * 3600.0, 200.0)  # absurdly hot -> would exceed max
    assert est.current_lag_seconds() == 8 * 3600.0


def test_temperature_dependent_delay_end_to_end():
    """A warm-weather estimate looks further back than a cold-weather one."""
    slope = 0.067 * 3600.0
    est = BulkTemperatureEstimator(
        lag_seconds=5 * 3600.0,
        lag_slope_seconds_per_degree=slope,
        reference_temperature=60.0,
        season_time_constant_seconds=1.0,
    )
    # Build a long rising ramp so the delayed lookup is well inside the buffer.
    for i in range(60):
        est.add(i * 3600.0, float(i))  # value == hour index
    now = 59 * 3600.0
    est_val = est.estimate(now)
    # season temp ~ latest (59); lag ~ 5 + 0.067*(59-60) ~ 4.93 h -> value ~ 59-4.93
    assert abs(est_val - (59 - 4.93)) < 0.6
