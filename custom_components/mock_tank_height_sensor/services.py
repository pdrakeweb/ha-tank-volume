"""Services for Mock Tank Height Sensor."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_VALUE = "set_value"

ATTR_ENTITY_ID = "entity_id"
ATTR_VALUE = "value"

SET_VALUE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_VALUE): vol.Coerce(float),
    }
)


def setup_services(hass: HomeAssistant) -> None:
    """Set up services for mock tank height sensor."""

    async def async_handle_set_value(call: ServiceCall) -> None:
        """Handle the set_value service call."""
        entity_id = call.data[ATTR_ENTITY_ID]
        value = call.data[ATTR_VALUE]

        # Get the entity state
        entity = hass.states.get(entity_id)
        if entity is None:
            _LOGGER.error("Entity %s not found", entity_id)
            return

        # Update the state directly via state machine
        # This is appropriate for a mock sensor that doesn't need complex
        # internal state management. The sensor will reflect this change
        # on its next state read.
        hass.states.async_set(
            entity_id,
            value,
            entity.attributes,
        )
        _LOGGER.debug("Set %s to %s", entity_id, value)

    hass.services.async_register(
        "mock_tank_height_sensor",
        SERVICE_SET_VALUE,
        async_handle_set_value,
        schema=SET_VALUE_SCHEMA,
    )
