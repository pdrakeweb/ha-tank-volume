"""Tests for Tank Volume Calculator volume calculation."""
import math
import pytest

from custom_components.tank_volume.sensor import (
    compute_horizontal_cylinder_volume_percentage,
)


def test_volume_calculation_empty():
    """Test volume calculation for empty tank (h = 0)."""
    result = compute_horizontal_cylinder_volume_percentage(0, 24)
    assert result == 0.0


def test_volume_calculation_half_full():
    """Test volume calculation for half-full tank (h = radius)."""
    diameter = 24
    fill_height = diameter / 2  # 12 inches
    result = compute_horizontal_cylinder_volume_percentage(fill_height, diameter)
    assert result is not None
    assert abs(result - 50.0) < 0.01  # Should be exactly 50%


def test_volume_calculation_full():
    """Test volume calculation for full tank (h = diameter)."""
    result = compute_horizontal_cylinder_volume_percentage(24, 24)
    assert result == 100.0


def test_volume_calculation_10_percent_height():
    """Test volume calculation at 10% of diameter."""
    diameter = 24
    fill_height = 0.1 * diameter
    result = compute_horizontal_cylinder_volume_percentage(fill_height, diameter)
    assert result is not None
    # At 10% height, volume should be approximately 5.2%
    assert abs(result - 5.2) < 0.5


def test_volume_calculation_25_percent_height():
    """Test volume calculation at 25% of diameter."""
    diameter = 24
    fill_height = 0.25 * diameter
    result = compute_horizontal_cylinder_volume_percentage(fill_height, diameter)
    assert result is not None
    # At 25% height, volume should be approximately 19.53%
    assert abs(result - 19.53) < 0.5


def test_volume_calculation_75_percent_height():
    """Test volume calculation at 75% of diameter."""
    diameter = 24
    fill_height = 0.75 * diameter
    result = compute_horizontal_cylinder_volume_percentage(fill_height, diameter)
    assert result is not None
    # At 75% height, volume should be approximately 80.47%
    assert abs(result - 80.47) < 0.5


def test_volume_calculation_90_percent_height():
    """Test volume calculation at 90% of diameter."""
    diameter = 24
    fill_height = 0.9 * diameter
    result = compute_horizontal_cylinder_volume_percentage(fill_height, diameter)
    assert result is not None
    # At 90% height, volume should be approximately 94.8%
    assert abs(result - 94.8) < 0.5


def test_volume_calculation_negative_height():
    """Test volume calculation with negative fill height (should clamp to 0%)."""
    result = compute_horizontal_cylinder_volume_percentage(-5, 24)
    assert result == 0.0


def test_volume_calculation_height_exceeds_diameter():
    """Test volume calculation when height exceeds diameter (should clamp to 100%)."""
    result = compute_horizontal_cylinder_volume_percentage(30, 24)
    assert result == 100.0


def test_volume_calculation_zero_diameter():
    """Test volume calculation with zero diameter (should return None)."""
    result = compute_horizontal_cylinder_volume_percentage(10, 0)
    assert result is None


def test_volume_calculation_negative_diameter():
    """Test volume calculation with negative diameter (should return None)."""
    result = compute_horizontal_cylinder_volume_percentage(10, -24)
    assert result is None


def test_volume_calculation_various_diameters():
    """Test that percentage is independent of tank diameter."""
    # At 50% height, should always be 50% volume regardless of diameter
    for diameter in [12, 24, 36, 48]:
        fill_height = diameter / 2
        result = compute_horizontal_cylinder_volume_percentage(fill_height, diameter)
        assert result is not None
        assert abs(result - 50.0) < 0.01
