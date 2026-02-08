"""Tests for Tank Volume Calculator volume calculation."""

import math

from custom_components.tank_volume.sensor import (
    compute_ellipsoidal_head_volume,
    compute_horizontal_cylinder_volume_percentage,
    compute_tank_volume_with_heads,
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


# Tests for ellipsoidal head volume calculations
def test_ellipsoidal_head_volume_empty():
    """Test ellipsoidal head volume at h = 0."""
    result = compute_ellipsoidal_head_volume(0, 12, 6)
    assert result == 0.0


def test_ellipsoidal_head_volume_full():
    """Test ellipsoidal head volume at h = diameter (full)."""
    radius = 12
    head_depth = 6
    diameter = 2 * radius
    result = compute_ellipsoidal_head_volume(diameter, radius, head_depth)

    # Should equal full head volume: (2/3) * π * r² * a
    expected = (2.0 / 3.0) * math.pi * radius * radius * head_depth
    assert abs(result - expected) < 0.01


def test_ellipsoidal_head_volume_2_1_ratio():
    """Test 2:1 ellipsoidal head volume calculation."""
    diameter = 48
    radius = diameter / 2  # 24
    head_depth = diameter / 4  # 12 (2:1 ratio)

    # Test at various fill heights
    # At h = 0
    result = compute_ellipsoidal_head_volume(0, radius, head_depth)
    assert result == 0.0

    # At h = diameter (full)
    result = compute_ellipsoidal_head_volume(diameter, radius, head_depth)
    expected_full = (2.0 / 3.0) * math.pi * radius * radius * head_depth
    assert abs(result - expected_full) < 0.01

    # At h = diameter/2 (half full)
    result = compute_ellipsoidal_head_volume(diameter / 2, radius, head_depth)
    assert abs(result - (expected_full / 2.0)) < 0.01


def test_ellipsoidal_head_volume_formula():
    """Test ellipsoidal head volume formula accuracy."""
    radius = 12
    head_depth = 6
    fill_height = 10

    # Integrated half-ellipsoid volume from bottom to height h
    y = fill_height - radius
    expected = 0.5 * math.pi * radius * head_depth * (y - (y**3) / (3.0 * radius * radius) + (2.0 / 3.0) * radius)
    result = compute_ellipsoidal_head_volume(fill_height, radius, head_depth)

    assert abs(result - expected) < 0.01


# Tests for tank with heads
def test_tank_with_heads_flat():
    """Test tank with flat end caps (backward compatibility)."""
    diameter = 24
    cylinder_length = 96
    fill_height = 12  # Half full

    result = compute_tank_volume_with_heads(fill_height, diameter, cylinder_length, "flat")

    # Should match pure cylinder calculation
    expected = compute_horizontal_cylinder_volume_percentage(fill_height, diameter)
    assert result is not None
    assert expected is not None
    assert abs(result - expected) < 0.01


def test_tank_with_heads_2_1_ellipsoidal_empty():
    """Test tank with 2:1 ellipsoidal heads at h = 0."""
    result = compute_tank_volume_with_heads(0, 48, 96, "ellipsoidal_2_1")
    assert result == 0.0


def test_tank_with_heads_2_1_ellipsoidal_full():
    """Test tank with 2:1 ellipsoidal heads at h = diameter."""
    result = compute_tank_volume_with_heads(48, 48, 96, "ellipsoidal_2_1")
    assert result == 100.0


def test_tank_with_heads_2_1_ellipsoidal_half():
    """Test tank with 2:1 ellipsoidal heads at h = diameter/2."""
    diameter = 48
    cylinder_length = 96
    fill_height = diameter / 2  # 24 inches

    result = compute_tank_volume_with_heads(fill_height, diameter, cylinder_length, "ellipsoidal_2_1")

    assert result is not None
    # At half height, total volume should be 50% for symmetric heads
    assert abs(result - 50.0) < 0.01


def test_tank_with_heads_invalid_diameter():
    """Test tank with heads with invalid diameter."""
    result = compute_tank_volume_with_heads(24, 0, 96, "ellipsoidal_2_1")
    assert result is None


def test_tank_with_heads_invalid_length():
    """Test tank with heads with invalid cylinder length."""
    result = compute_tank_volume_with_heads(24, 48, 0, "ellipsoidal_2_1")
    assert result is None


def test_tank_with_heads_negative_height():
    """Test tank with heads with negative fill height (should clamp to 0%)."""
    result = compute_tank_volume_with_heads(-5, 48, 96, "ellipsoidal_2_1")
    assert result == 0.0


def test_tank_with_heads_height_exceeds_diameter():
    """Test tank with heads when height exceeds diameter (should clamp to 100%)."""
    result = compute_tank_volume_with_heads(60, 48, 96, "ellipsoidal_2_1")
    assert result == 100.0


def test_tank_with_heads_various_heights():
    """Test tank with 2:1 ellipsoidal heads at various fill heights."""
    diameter = 48
    cylinder_length = 96

    # Test multiple fill heights to ensure monotonic increase
    previous_percentage = 0.0
    for height_fraction in [0.1, 0.25, 0.5, 0.75, 0.9]:
        fill_height = diameter * height_fraction
        result = compute_tank_volume_with_heads(fill_height, diameter, cylinder_length, "ellipsoidal_2_1")
        assert result is not None
        assert result > previous_percentage  # Should increase monotonically
        previous_percentage = result


def test_backward_compatibility_flat_caps():
    """Test that flat end caps with length equal to diameter gives same result as pure cylinder."""
    diameter = 24
    fill_height = 15

    # Pure cylinder calculation
    pure_cylinder = compute_horizontal_cylinder_volume_percentage(fill_height, diameter)

    # Tank with flat heads and cylinder length = diameter (equivalent to pure cylinder)
    with_flat_heads = compute_tank_volume_with_heads(fill_height, diameter, diameter, "flat")

    assert pure_cylinder is not None
    assert with_flat_heads is not None
    assert abs(pure_cylinder - with_flat_heads) < 0.01
