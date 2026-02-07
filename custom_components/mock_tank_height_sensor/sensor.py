"""Mock Tank Height Sensor platform for testing."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_NAME,
    UnitOfLength,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

CONF_INITIAL_VALUE = "initial_value"
DEFAULT_NAME = "Mock Tank Height"
DEFAULT_INITIAL_VALUE = 0.0


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Mock Tank Height Sensor platform."""
    name = config.get(CONF_NAME, DEFAULT_NAME)
    initial_value = config.get(CONF_INITIAL_VALUE, DEFAULT_INITIAL_VALUE)

    sensor = MockTankHeightSensor(name, initial_value)
    async_add_entities([sensor], True)


class MockTankHeightSensor(SensorEntity):
    """Mock sensor that provides tank height in inches."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.INCHES
    _attr_icon = "mdi:ruler"
    _attr_suggested_display_precision = 1

    def __init__(self, name: str, initial_value: float) -> None:
        """Initialize the mock sensor."""
        self._attr_name = name
        self._attr_native_value = initial_value
        self._attr_unique_id = f"mock_tank_height_{name.lower().replace(' ', '_')}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "description": "Mock sensor for testing tank volume calculations",
            "editable": True,
        }

    async def async_set_value(self, value: float) -> None:
        """Set the sensor value (for programmatic control)."""
        self._attr_native_value = value
        self.async_write_ha_state()
