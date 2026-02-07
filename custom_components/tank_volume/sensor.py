"""Tank Volume Calculator sensor platform."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, PERCENTAGE
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_SOURCE_ENTITY, CONF_TANK_DIAMETER, DOMAIN

_LOGGER = logging.getLogger(__name__)


def compute_horizontal_cylinder_volume_percentage(
    fill_height_inches: float, diameter_inches: float
) -> float | None:
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

        # Calculate percentage
        percentage = (segment_area / circle_area) * 100.0

        return percentage
    except (ValueError, ZeroDivisionError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tank Volume Calculator sensor from a config entry."""
    source_entity = config_entry.data[CONF_SOURCE_ENTITY]
    tank_diameter = config_entry.options.get(
        CONF_TANK_DIAMETER, config_entry.data[CONF_TANK_DIAMETER]
    )
    name = config_entry.data[CONF_NAME]

    sensor = TankVolumeSensor(
        config_entry.entry_id,
        name,
        source_entity,
        tank_diameter,
    )

    async_add_entities([sensor], True)


class TankVolumeSensor(SensorEntity):
    """Representation of a Tank Volume Calculator sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:storage-tank"
    _attr_suggested_display_precision = 1
    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        name: str,
        source_entity: str,
        tank_diameter: float,
    ) -> None:
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._attr_name = name
        self._source_entity = source_entity
        self._tank_diameter = tank_diameter
        self._fill_height: float | None = None
        self._attr_unique_id = f"{entry_id}_volume_percentage"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._attr_name,
            manufacturer="Tank Volume Calculator",
            model="Horizontal Cylinder",
            entry_type=None,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "source_entity": self._source_entity,
            "tank_diameter_inches": self._tank_diameter,
            "fill_height_inches": self._fill_height,
        }

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()

        # Read current state of source entity
        if (state := self.hass.states.get(self._source_entity)) is not None:
            self._handle_source_state(state.state)

        # Track state changes
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._source_entity], self._async_source_changed
            )
        )

    @callback
    def _async_source_changed(self, event: Event) -> None:
        """Handle source entity state changes."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        self._handle_source_state(new_state.state)
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

            # Calculate volume percentage
            percentage = compute_horizontal_cylinder_volume_percentage(
                fill_height, self._tank_diameter
            )
            self._attr_native_value = percentage
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Unable to parse source entity state '%s' as a number", state_value
            )
            self._attr_native_value = None
            self._fill_height = None
