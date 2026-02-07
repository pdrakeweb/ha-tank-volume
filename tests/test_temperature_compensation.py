"""Tests for temperature compensation."""
import pytest

from homeassistant.const import UnitOfTemperature

from custom_components.tank_volume.sensor import apply_temperature_compensation


def test_temperature_compensation_fahrenheit_at_reference():
    """Test temperature compensation at reference temperature (60°F)."""
    # At reference temperature, no compensation should be applied
    result = apply_temperature_compensation(
        volume_percentage=50.0,
        temperature=60.0,
        temperature_unit=UnitOfTemperature.FAHRENHEIT,
    )
    assert result == pytest.approx(50.0, rel=1e-6)


def test_temperature_compensation_fahrenheit_above_reference():
    """Test temperature compensation above reference temperature."""
    # At higher temperature, liquid expands, so volume at reference should be lower
    # At 80°F (20°F above reference), with β=0.00205/°F:
    # compensation_factor = 1 / (1 + 0.00205 * 20) = 1 / 1.041 ≈ 0.9606
    result = apply_temperature_compensation(
        volume_percentage=50.0,
        temperature=80.0,
        temperature_unit=UnitOfTemperature.FAHRENHEIT,
    )
    expected = 50.0 * (1.0 / (1.0 + 0.00205 * 20))
    assert result == pytest.approx(expected, rel=1e-4)
    # Should be about 48.03%
    assert result < 50.0


def test_temperature_compensation_fahrenheit_below_reference():
    """Test temperature compensation below reference temperature."""
    # At lower temperature, liquid contracts, so volume at reference should be higher
    # At 40°F (20°F below reference), with β=0.00205/°F:
    # compensation_factor = 1 / (1 + 0.00205 * (-20)) = 1 / 0.959 ≈ 1.0427
    result = apply_temperature_compensation(
        volume_percentage=50.0,
        temperature=40.0,
        temperature_unit=UnitOfTemperature.FAHRENHEIT,
    )
    expected = 50.0 * (1.0 / (1.0 + 0.00205 * (-20)))
    assert result == pytest.approx(expected, rel=1e-4)
    # Should be about 52.14%
    assert result > 50.0


def test_temperature_compensation_celsius_at_reference():
    """Test temperature compensation at reference temperature (15°C)."""
    # At reference temperature, no compensation should be applied
    result = apply_temperature_compensation(
        volume_percentage=50.0,
        temperature=15.0,
        temperature_unit=UnitOfTemperature.CELSIUS,
    )
    assert result == pytest.approx(50.0, rel=1e-6)


def test_temperature_compensation_celsius_above_reference():
    """Test temperature compensation above reference temperature."""
    # At 25°C (10°C above reference), with β=0.00369/°C:
    # compensation_factor = 1 / (1 + 0.00369 * 10) = 1 / 1.0369 ≈ 0.9644
    result = apply_temperature_compensation(
        volume_percentage=50.0,
        temperature=25.0,
        temperature_unit=UnitOfTemperature.CELSIUS,
    )
    expected = 50.0 * (1.0 / (1.0 + 0.00369 * 10))
    assert result == pytest.approx(expected, rel=1e-4)
    # Should be about 48.22%
    assert result < 50.0


def test_temperature_compensation_celsius_below_reference():
    """Test temperature compensation below reference temperature."""
    # At 5°C (10°C below reference), with β=0.00369/°C:
    # compensation_factor = 1 / (1 + 0.00369 * (-10)) = 1 / 0.9631 ≈ 1.0383
    result = apply_temperature_compensation(
        volume_percentage=50.0,
        temperature=5.0,
        temperature_unit=UnitOfTemperature.CELSIUS,
    )
    expected = 50.0 * (1.0 / (1.0 + 0.00369 * (-10)))
    assert result == pytest.approx(expected, rel=1e-4)
    # Should be about 51.92%
    assert result > 50.0


def test_temperature_compensation_extreme_cold():
    """Test temperature compensation at extreme cold temperature."""
    # At -20°F (80°F below reference)
    result = apply_temperature_compensation(
        volume_percentage=75.0,
        temperature=-20.0,
        temperature_unit=UnitOfTemperature.FAHRENHEIT,
    )
    expected = 75.0 * (1.0 / (1.0 + 0.00205 * (-80)))
    assert result == pytest.approx(expected, rel=1e-4)
    # Should be higher than measured
    assert result > 75.0


def test_temperature_compensation_extreme_heat():
    """Test temperature compensation at extreme heat temperature."""
    # At 100°F (40°F above reference)
    result = apply_temperature_compensation(
        volume_percentage=75.0,
        temperature=100.0,
        temperature_unit=UnitOfTemperature.FAHRENHEIT,
    )
    expected = 75.0 * (1.0 / (1.0 + 0.00205 * 40))
    assert result == pytest.approx(expected, rel=1e-4)
    # Should be lower than measured
    assert result < 75.0


def test_temperature_compensation_zero_volume():
    """Test temperature compensation with zero volume."""
    result = apply_temperature_compensation(
        volume_percentage=0.0,
        temperature=80.0,
        temperature_unit=UnitOfTemperature.FAHRENHEIT,
    )
    assert result == pytest.approx(0.0, rel=1e-6)


def test_temperature_compensation_full_volume():
    """Test temperature compensation with full volume."""
    result = apply_temperature_compensation(
        volume_percentage=100.0,
        temperature=80.0,
        temperature_unit=UnitOfTemperature.FAHRENHEIT,
    )
    expected = 100.0 * (1.0 / (1.0 + 0.00205 * 20))
    assert result == pytest.approx(expected, rel=1e-4)
