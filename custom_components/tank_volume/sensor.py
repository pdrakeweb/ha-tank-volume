"""Tank Volume Calculator sensor platform."""

from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, CONF_NAME, PERCENTAGE, UnitOfTemperature, UnitOfVolume
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ADJUSTMENT_COEFFICIENT,
    CONF_CYLINDER_LENGTH,
    CONF_END_CAP_TYPE,
    CONF_SOURCE_ENTITY,
    CONF_TANK_DIAMETER,
    CONF_TANK_TOTAL_LENGTH,
    CONF_TANK_VOLUME,
    CONF_TEMPERATURE_ENTITY,
    CONF_TEMPERATURE_LAG_HOURS,
    CONF_TEMPERATURE_LAG_PER_DEGREE,
    CONF_TEMPERATURE_SMOOTHING_HOURS,
    DEFAULT_ADJUSTMENT_COEFFICIENT,
    DEFAULT_TEMPERATURE_LAG_HOURS,
    DEFAULT_TEMPERATURE_LAG_PER_DEGREE,
    DEFAULT_TEMPERATURE_SMOOTHING_HOURS,
    DOMAIN,
    END_CAP_ELLIPSOIDAL_2_1,
    END_CAP_FLAT,
    MAX_TEMPERATURE_LAG_HOURS,
    MIN_TEMPERATURE_LAG_HOURS,
    PROPANE_EXPANSION_COEFFICIENT_F,
    REFERENCE_TEMPERATURE_F,
    TEMPERATURE_LAG_SEASON_TIME_CONSTANT_HOURS,
)
from .temperature import BulkTemperatureEstimator

SECONDS_PER_HOUR = 3600.0

_LOGGER = logging.getLogger(__name__)

MEASUREMENT_CONTENTS_VOLUME = "contents_volume"
MEASUREMENT_FILL_LEVEL = "fill_level"


def compute_horizontal_cylinder_volume_percentage(fill_height_inches: float, diameter_inches: float) -> float | None:
    """
    Calculate the volumetric fill percentage for a horizontal cylindrical tank.

    For a horizontal cylinder with radius r and liquid fill height h:
    The cross-sectional area of the liquid is a circular segment:
    A(h) = r² · arccos((r - h) / r) - (r - h) · √(2rh - h²)

    The full circle area is π · r²
    Volumetric fill percentage = A(h) / (π · r²) × 100

    Args:
        fill_height_inches: The liquid fill height in inches (0 ≤ h ≤ diameter)
        diameter_inches: The tank internal diameter in inches

    Returns:
        The volumetric fill percentage (0-100), or None if diameter is invalid
    """
    # Validate diameter
    if diameter_inches <= 0:
        return None

    # Clamp fill height to valid range
    h = max(0, min(fill_height_inches, diameter_inches))
    r = diameter_inches / 2.0

    # Handle edge cases
    if h <= 0:
        return 0.0
    if h >= diameter_inches:
        return 100.0

    # Calculate the circular segment area
    # A(h) = r² · arccos((r - h) / r) - (r - h) · √(2rh - h²)
    try:
        # First term: r² · arccos((r - h) / r)
        arccos_term = r * r * math.acos((r - h) / r)

        # Second term: (r - h) · √(2rh - h²)
        sqrt_term = (r - h) * math.sqrt(2 * r * h - h * h)

        # Circular segment area
        segment_area = arccos_term - sqrt_term

        # Full circle area
        circle_area = math.pi * r * r
    except (ValueError, ZeroDivisionError):
        return None
    else:
        return (segment_area / circle_area) * 100.0


def compute_ellipsoidal_head_volume(
    fill_height: float,
    radius: float,
    head_depth: float,
) -> float:
    """
    Calculate liquid volume in one semi-ellipsoidal head at given fill height.

    Args:
        fill_height: Liquid height in the tank (0 to diameter)
        radius: Tank radius (diameter / 2)
        head_depth: Depth of the ellipsoidal head

    Returns:
        Volume in cubic inches (or same unit³ as inputs)
    """
    if fill_height <= 0:
        return 0.0

    diameter = 2 * radius
    if fill_height >= diameter:
        # Full head - return total volume
        return (2.0 / 3.0) * math.pi * radius * radius * head_depth

    h = max(0.0, min(fill_height, diameter))
    r = radius
    a = head_depth

    # Integrate half-ellipsoid cross-section areas from y = -r to y = -r + h.
    # Volume = 0.5 * pi * r * a * (y - y^3 / (3 r^2)) |_{-r}^{h - r}
    y = h - r
    return 0.5 * math.pi * r * a * (y - (y**3) / (3.0 * r * r) + (2.0 / 3.0) * r)


def compute_tank_volume_with_heads(
    fill_height: float,
    diameter: float,
    cylinder_length: float,
    end_cap_type: str = END_CAP_FLAT,
) -> float | None:
    """
    Calculate volumetric fill percentage for horizontal tank with optional ellipsoidal heads.

    Args:
        fill_height: Liquid fill height in inches
        diameter: Tank diameter in inches
        cylinder_length: Length of cylindrical section in inches
        end_cap_type: "flat" or "ellipsoidal_2_1"

    Returns:
        Fill percentage (0-100) or None if invalid
    """
    # Validate inputs
    if diameter <= 0 or cylinder_length <= 0:
        return None

    # Clamp fill height to valid range
    h = max(0.0, min(fill_height, diameter))
    r = diameter / 2.0

    # Handle edge cases
    if h <= 0:
        return 0.0
    if h >= diameter:
        return 100.0

    # Calculate cylinder cross-sectional area (circular segment)
    try:
        # First term: r² · arccos((r - h) / r)
        arccos_term = r * r * math.acos((r - h) / r)

        # Second term: (r - h) · √(2rh - h²)
        sqrt_term = (r - h) * math.sqrt(2 * r * h - h * h)

        # Circular segment area
        segment_area = arccos_term - sqrt_term

        # Cylinder volume
        cylinder_volume = segment_area * cylinder_length

        # Calculate head volumes based on end cap type
        if end_cap_type == END_CAP_FLAT:
            # No end caps - pure cylinder
            head_volume = 0.0
            total_head_volume = 0.0
        elif end_cap_type == END_CAP_ELLIPSOIDAL_2_1:
            # Standard 2:1 ellipsoidal heads
            head_depth = r / 2.0  # For 2:1 ratio, depth = diameter/4 = radius/2
            head_volume = 2.0 * compute_ellipsoidal_head_volume(h, r, head_depth)
            total_head_volume = 2.0 * (2.0 / 3.0) * math.pi * r * r * head_depth
        else:
            return None

        # Total volume at fill height h
        total_volume = cylinder_volume + head_volume

        # Total tank capacity
        circle_area = math.pi * r * r
        total_capacity = circle_area * cylinder_length + total_head_volume
    except (ValueError, ZeroDivisionError):
        return None
    else:
        return (total_volume / total_capacity) * 100.0


def compute_temperature_compensated_percentage(
    volume_percentage: float,
    temperature: float,
    unit: UnitOfTemperature,
    coefficient: float = PROPANE_EXPANSION_COEFFICIENT_F,
) -> float | None:
    """Adjust volume percentage to reference temperature using propane expansion."""
    if unit == UnitOfTemperature.FAHRENHEIT:
        reference_temperature = REFERENCE_TEMPERATURE_F
        temperature_value = temperature
    elif unit == UnitOfTemperature.CELSIUS:
        reference_temperature = REFERENCE_TEMPERATURE_F
        temperature_value = (temperature * 9.0 / 5.0) + 32.0
    else:
        return None

    adjustment_factor = 1.0 + (temperature_value - reference_temperature) * coefficient
    if adjustment_factor <= 0.0:
        return None

    adjusted_percentage = volume_percentage / adjustment_factor
    return max(0.0, min(100.0, adjusted_percentage))


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tank Volume Calculator sensor from a config entry."""
    source_entity = config_entry.data[CONF_SOURCE_ENTITY]
    tank_diameter = config_entry.options.get(CONF_TANK_DIAMETER, config_entry.data[CONF_TANK_DIAMETER])
    tank_total_length = config_entry.options.get(
        CONF_TANK_TOTAL_LENGTH,
        config_entry.data.get(CONF_TANK_TOTAL_LENGTH),
    )
    tank_volume = config_entry.options.get(CONF_TANK_VOLUME, config_entry.data.get(CONF_TANK_VOLUME))
    name = config_entry.data[CONF_NAME]
    temperature_entity = config_entry.options.get(
        CONF_TEMPERATURE_ENTITY,
        config_entry.data.get(CONF_TEMPERATURE_ENTITY),
    )
    adjustment_coefficient = config_entry.options.get(
        CONF_ADJUSTMENT_COEFFICIENT,
        config_entry.data.get(CONF_ADJUSTMENT_COEFFICIENT, DEFAULT_ADJUSTMENT_COEFFICIENT),
    )
    temperature_lag_hours = config_entry.options.get(
        CONF_TEMPERATURE_LAG_HOURS,
        config_entry.data.get(CONF_TEMPERATURE_LAG_HOURS, DEFAULT_TEMPERATURE_LAG_HOURS),
    )
    temperature_lag_per_degree = config_entry.options.get(
        CONF_TEMPERATURE_LAG_PER_DEGREE,
        config_entry.data.get(CONF_TEMPERATURE_LAG_PER_DEGREE, DEFAULT_TEMPERATURE_LAG_PER_DEGREE),
    )
    temperature_smoothing_hours = config_entry.options.get(
        CONF_TEMPERATURE_SMOOTHING_HOURS,
        config_entry.data.get(CONF_TEMPERATURE_SMOOTHING_HOURS, DEFAULT_TEMPERATURE_SMOOTHING_HOURS),
    )

    # Get end cap configuration
    end_cap_type = config_entry.options.get(
        CONF_END_CAP_TYPE, config_entry.data.get(CONF_END_CAP_TYPE, END_CAP_ELLIPSOIDAL_2_1)
    )
    cylinder_length = config_entry.options.get(CONF_CYLINDER_LENGTH, config_entry.data.get(CONF_CYLINDER_LENGTH))

    sensors: list[TankVolumeSensor] = [
        TankVolumeSensor(
            config_entry.entry_id,
            name,
            "Fill level",
            MEASUREMENT_FILL_LEVEL,
            source_entity,
            None,
            tank_diameter,
            tank_total_length,
            tank_volume,
            end_cap_type,
            cylinder_length,
            adjustment_coefficient,
            apply_temperature_compensation=False,
        ),
        TankVolumeSensor(
            config_entry.entry_id,
            name,
            "Contents volume",
            MEASUREMENT_CONTENTS_VOLUME,
            source_entity,
            None,
            tank_diameter,
            tank_total_length,
            tank_volume,
            end_cap_type,
            cylinder_length,
            adjustment_coefficient,
            apply_temperature_compensation=False,
        ),
    ]

    if temperature_entity:
        sensors.extend(
            [
                TankVolumeSensor(
                    config_entry.entry_id,
                    name,
                    "Fill level (temperature adjusted)",
                    MEASUREMENT_FILL_LEVEL,
                    source_entity,
                    temperature_entity,
                    tank_diameter,
                    tank_total_length,
                    tank_volume,
                    end_cap_type,
                    cylinder_length,
                    adjustment_coefficient,
                    apply_temperature_compensation=True,
                    temperature_lag_hours=temperature_lag_hours,
                    temperature_lag_per_degree=temperature_lag_per_degree,
                    temperature_smoothing_hours=temperature_smoothing_hours,
                ),
                TankVolumeSensor(
                    config_entry.entry_id,
                    name,
                    "Contents volume (temperature adjusted)",
                    MEASUREMENT_CONTENTS_VOLUME,
                    source_entity,
                    temperature_entity,
                    tank_diameter,
                    tank_total_length,
                    tank_volume,
                    end_cap_type,
                    cylinder_length,
                    adjustment_coefficient,
                    apply_temperature_compensation=True,
                    temperature_lag_hours=temperature_lag_hours,
                    temperature_lag_per_degree=temperature_lag_per_degree,
                    temperature_smoothing_hours=temperature_smoothing_hours,
                ),
            ]
        )

    async_add_entities(sensors, True)


class TankVolumeSensor(SensorEntity):
    """Representation of a Tank Volume Calculator sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:storage-tank"
    _attr_suggested_display_precision = 1
    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        name: str,
        measurement_type: str,
        source_entity: str,
        temperature_entity: str | None,
        tank_diameter: float,
        tank_total_length: float | None,
        tank_volume: float | None,
        end_cap_type: str = END_CAP_ELLIPSOIDAL_2_1,
        cylinder_length: float | None = None,
        adjustment_coefficient: float = DEFAULT_ADJUSTMENT_COEFFICIENT,
        apply_temperature_compensation: bool = False,
        temperature_lag_hours: float = 0.0,
        temperature_lag_per_degree: float = 0.0,
        temperature_smoothing_hours: float = 0.0,
    ) -> None:
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._attr_name = name
        self._device_name = device_name
        self._measurement_type = measurement_type
        self._source_entity = source_entity
        self._temperature_entity = temperature_entity
        self._apply_temperature_compensation = apply_temperature_compensation
        self._tank_diameter = tank_diameter
        self._tank_total_length = tank_total_length
        self._tank_volume = tank_volume
        self._end_cap_type = end_cap_type
        self._cylinder_length = cylinder_length
        self._adjustment_coefficient = adjustment_coefficient
        self._temperature_lag_hours = max(0.0, temperature_lag_hours or 0.0)
        self._temperature_lag_per_degree = temperature_lag_per_degree or 0.0
        self._temperature_smoothing_hours = max(0.0, temperature_smoothing_hours or 0.0)
        self._fill_height: float | None = None
        self._temperature_value: float | None = None
        self._temperature_unit: UnitOfTemperature | None = None
        # Estimator reconstructs the lagged bulk temperature that actually drives the
        # liquid's expansion. The transport delay is temperature dependent (it grows in
        # warmer weather). Only built when compensation is active and some lag is
        # configured; otherwise the instantaneous reading is used.
        self._temperature_estimator: BulkTemperatureEstimator | None = None
        if self._apply_temperature_compensation and (
            self._temperature_lag_hours > 0.0 or self._temperature_lag_per_degree != 0.0
        ):
            self._temperature_estimator = BulkTemperatureEstimator(
                lag_seconds=self._temperature_lag_hours * SECONDS_PER_HOUR,
                smoothing_seconds=self._temperature_smoothing_hours * SECONDS_PER_HOUR,
                lag_slope_seconds_per_degree=self._temperature_lag_per_degree * SECONDS_PER_HOUR,
                reference_temperature=REFERENCE_TEMPERATURE_F,
                min_lag_seconds=MIN_TEMPERATURE_LAG_HOURS * SECONDS_PER_HOUR,
                max_lag_seconds=MAX_TEMPERATURE_LAG_HOURS * SECONDS_PER_HOUR,
                season_time_constant_seconds=TEMPERATURE_LAG_SEASON_TIME_CONSTANT_HOURS * SECONDS_PER_HOUR,
            )
        if self._measurement_type == MEASUREMENT_CONTENTS_VOLUME:
            unique_suffix = "contents_volume"
        else:
            unique_suffix = "fill_level"
        if self._apply_temperature_compensation:
            unique_suffix = f"temperature_adjusted_{unique_suffix}"
        self._attr_unique_id = f"{entry_id}_{unique_suffix}"
        self._attr_native_unit_of_measurement = (
            PERCENTAGE if self._measurement_type == MEASUREMENT_FILL_LEVEL else UnitOfVolume.GALLONS
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._device_name,
            manufacturer="Tank Volume Calculator",
            model="Horizontal Cylinder",
            entry_type=None,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {
            "source_entity": self._source_entity,
            "tank_diameter_inches": self._tank_diameter,
            "tank_total_length_inches": self._tank_total_length,
            "tank_volume_gallons": self._tank_volume,
            "fill_height_inches": self._fill_height,
            "end_cap_type": self._end_cap_type,
            "adjustment_coefficient": self._adjustment_coefficient,
        }
        if self._temperature_entity is not None:
            attrs["temperature_entity"] = self._temperature_entity
        if self._temperature_value is not None and self._temperature_unit is not None:
            attrs["temperature_value"] = self._temperature_value
            attrs["temperature_unit"] = self._temperature_unit
        if self._apply_temperature_compensation:
            attrs["temperature_adjusted"] = True
            if self._temperature_estimator is not None:
                attrs["temperature_lag_hours"] = self._temperature_lag_hours
                attrs["temperature_lag_per_degree"] = self._temperature_lag_per_degree
                attrs["temperature_smoothing_hours"] = self._temperature_smoothing_hours
                # Effective (temperature-dependent) lag currently in effect.
                attrs["effective_lag_hours"] = round(
                    self._temperature_estimator.current_lag_seconds() / SECONDS_PER_HOUR, 2
                )
                estimate = self._temperature_estimator.estimate(dt_util.utcnow().timestamp())
                if estimate is not None:
                    attrs["bulk_temperature_f"] = round(estimate, 2)
        if self._cylinder_length is not None:
            attrs["cylinder_length_inches"] = self._cylinder_length
        return attrs

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()

        # Read current state of source entity
        if (state := self.hass.states.get(self._source_entity)) is not None:
            self._handle_source_state(state.state)

        if self._temperature_entity and (state := self.hass.states.get(self._temperature_entity)) is not None:
            self._handle_temperature_state(state)
            self._recalculate_value()

        # Track state changes
        entities_to_track = [self._source_entity]
        if self._temperature_entity:
            entities_to_track.append(self._temperature_entity)

        self.async_on_remove(async_track_state_change_event(self.hass, entities_to_track, self._async_source_changed))

    @callback
    def _async_source_changed(self, event: Event[EventStateChangedData]) -> None:
        """Handle source entity state changes."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        if new_state.entity_id == self._source_entity:
            self._handle_source_state(new_state.state)
        elif self._temperature_entity and new_state.entity_id == self._temperature_entity:
            self._handle_temperature_state(new_state)
            self._recalculate_value()
        self.async_write_ha_state()

    def _handle_source_state(self, state_value: str) -> None:
        """Handle source entity state value."""
        # Handle unavailable or unknown states
        if state_value in ("unknown", "unavailable", None):
            self._attr_native_value = None
            self._fill_height = None
            return

        # Try to parse as float
        try:
            fill_height = float(state_value)
            self._fill_height = fill_height

            self._recalculate_value()
        except (ValueError, TypeError):
            _LOGGER.warning("Unable to parse source entity state '%s' as a number", state_value)
            self._attr_native_value = None
            self._fill_height = None

    def _handle_temperature_state(self, state: Any) -> None:
        """Handle temperature entity state and unit."""
        if state.state in ("unknown", "unavailable", None):
            self._temperature_value = None
            self._temperature_unit = None
            return

        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        if unit not in (UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS):
            self._temperature_value = None
            self._temperature_unit = None
            return

        try:
            value = float(state.state)
        except (ValueError, TypeError):
            self._temperature_value = None
            self._temperature_unit = None
            return

        self._temperature_value = value
        self._temperature_unit = UnitOfTemperature(unit)

        # Feed the lag estimator, normalising to Fahrenheit for a single internal unit.
        if self._temperature_estimator is not None:
            temperature_f = (
                value if self._temperature_unit == UnitOfTemperature.FAHRENHEIT else value * 9.0 / 5.0 + 32.0
            )
            timestamp = (
                state.last_updated.timestamp() if state.last_updated is not None else dt_util.utcnow().timestamp()
            )
            self._temperature_estimator.add(timestamp, temperature_f)

    def _effective_temperature(self) -> tuple[float | None, UnitOfTemperature | None]:
        """Return the temperature used for compensation.

        When a lag estimator is active it returns the estimated bulk temperature in
        Fahrenheit; otherwise (lag disabled or estimator not yet seeded) it falls back
        to the latest instantaneous reading, preserving the legacy behaviour.
        """
        if self._temperature_estimator is not None:
            estimate = self._temperature_estimator.estimate(dt_util.utcnow().timestamp())
            if estimate is not None:
                return estimate, UnitOfTemperature.FAHRENHEIT
        if self._temperature_value is not None and self._temperature_unit is not None:
            return self._temperature_value, self._temperature_unit
        return None, None

    def _recalculate_value(self) -> None:
        """Recalculate fill level or contents volume using current fill height and temperature."""
        if self._fill_height is None:
            self._attr_native_value = None
            return

        if self._end_cap_type == END_CAP_FLAT:
            percentage = compute_horizontal_cylinder_volume_percentage(self._fill_height, self._tank_diameter)
        else:
            cylinder_length = self._cylinder_length or self._tank_diameter
            percentage = compute_tank_volume_with_heads(
                self._fill_height,
                self._tank_diameter,
                cylinder_length,
                self._end_cap_type,
            )

        if percentage is None:
            self._attr_native_value = None
            return

        if self._apply_temperature_compensation:
            effective_temp, effective_unit = self._effective_temperature()
            if effective_temp is not None and effective_unit is not None:
                adjusted = compute_temperature_compensated_percentage(
                    percentage,
                    effective_temp,
                    effective_unit,
                    self._adjustment_coefficient,
                )
                percentage = adjusted if adjusted is not None else percentage

        if self._measurement_type == MEASUREMENT_CONTENTS_VOLUME:
            if self._tank_volume is None or self._tank_volume <= 0:
                self._attr_native_value = None
                return
            self._attr_native_value = (percentage / 100.0) * self._tank_volume
            return

        self._attr_native_value = percentage
