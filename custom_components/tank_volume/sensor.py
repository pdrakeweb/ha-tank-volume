"""Sensor platform for Tank Volume Calculator."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_NAME,
    CONF_SOURCE_ENTITY,
    CONF_TANK_DIAMETER,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def compute_horizontal_cylinder_volume_percentage(
    fill_height_inches: float, diameter_inches: float
) -> float | None:
    """
    Calculate volumetric fill percentage for a horizontal cylindrical tank.
    
    Args:
        fill_height_inches: The liquid fill height in inches
        diameter_inches: The tank internal diameter in inches
        
    Returns:
        The volumetric fill percentage (0-100), or None if invalid inputs
    """
    # Validate diameter
    if diameter_inches <= 0:
        return None
    
    # Clamp fill height to valid range
    h = max(0.0, min(fill_height_inches, diameter_inches))
    
    # Calculate radius
    r = diameter_inches / 2.0
    
    # Handle edge cases
    if h <= 0:
        return 0.0
    if h >= diameter_inches:
        return 100.0
    
    # Calculate circular segment area using the formula:
    # A(h) = r² · arccos((r - h) / r) - (r - h) · √(2rh - h²)
    try:
        term1 = r * r * math.acos((r - h) / r)
        term2 = (r - h) * math.sqrt(2 * r * h - h * h)
        segment_area = term1 - term2
        
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
    """Set up the Tank Volume sensor from a config entry."""
    async_add_entities(
        [TankVolumeSensor(hass, config_entry)],
        True,
    )


class TankVolumeSensor(SensorEntity):
    """Representation of a Tank Volume sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:storage-tank"
    _attr_suggested_display_precision = 1
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the Tank Volume sensor."""
        self.hass = hass
        self._config_entry = config_entry
        self._attr_unique_id = config_entry.entry_id
        self._attr_name = None  # Use device name
        
        # Get configuration
        self._source_entity_id = config_entry.data[CONF_SOURCE_ENTITY]
        self._tank_diameter = config_entry.data[CONF_TANK_DIAMETER]
        self._sensor_name = config_entry.data[CONF_NAME]
        
        # State tracking
        self._attr_native_value = None
        self._fill_height = None
        self._attr_available = True
        
        # Set up device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=self._sensor_name,
            manufacturer="Tank Volume Calculator",
            model="Horizontal Cylinder",
            entry_type=None,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "source_entity": self._source_entity_id,
            "tank_diameter_inches": self._tank_diameter,
            "fill_height_inches": self._fill_height,
        }

    async def async_added_to_hass(self) -> None:
        """Handle entity added to Home Assistant."""
        await super().async_added_to_hass()
        
        # Read current state immediately
        await self._async_update_from_source()
        
        # Track state changes
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._source_entity_id],
                self._async_source_changed,
            )
        )

    @callback
    def _async_source_changed(self, event: Event) -> None:
        """Handle source entity state changes."""
        self.hass.async_create_task(self._async_update_from_source())

    async def _async_update_from_source(self) -> None:
        """Update sensor value from source entity."""
        source_state = self.hass.states.get(self._source_entity_id)
        
        if source_state is None:
            _LOGGER.warning(
                "Source entity %s not found", self._source_entity_id
            )
            self._attr_available = False
            self._attr_native_value = None
            self._fill_height = None
            self.async_write_ha_state()
            return
        
        # Handle unavailable/unknown states
        if source_state.state in ("unavailable", "unknown", None):
            self._attr_available = False
            self._attr_native_value = None
            self._fill_height = None
            self.async_write_ha_state()
            return
        
        # Try to parse numeric value
        try:
            fill_height = float(source_state.state)
            self._fill_height = fill_height
            
            # Calculate volume percentage
            percentage = compute_horizontal_cylinder_volume_percentage(
                fill_height, self._tank_diameter
            )
            
            if percentage is not None:
                self._attr_native_value = percentage
                self._attr_available = True
            else:
                self._attr_native_value = None
                self._attr_available = False
                _LOGGER.error(
                    "Invalid calculation for fill_height=%s, diameter=%s",
                    fill_height,
                    self._tank_diameter,
                )
        except (ValueError, TypeError) as err:
            _LOGGER.warning(
                "Could not parse source entity %s state '%s': %s",
                self._source_entity_id,
                source_state.state,
                err,
            )
            self._attr_available = False
            self._attr_native_value = None
            self._fill_height = None
        
        self.async_write_ha_state()
