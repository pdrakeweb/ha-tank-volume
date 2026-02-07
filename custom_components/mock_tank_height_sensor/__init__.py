"""Mock Tank Height Sensor for testing purposes."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .services import setup_services

_LOGGER = logging.getLogger(__name__)

DOMAIN = "mock_tank_height_sensor"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Mock Tank Height Sensor component."""
    setup_services(hass)
    return True
