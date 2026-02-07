"""Config flow for Tank Volume Calculator integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.typing import ConfigFlowResult

from .const import (
    CONF_SOURCE_ENTITY,
    CONF_TANK_DIAMETER,
    DEFAULT_NAME,
    DOMAIN,
)


class TankVolumeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tank Volume Calculator."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate tank diameter
            if user_input[CONF_TANK_DIAMETER] <= 0:
                errors[CONF_TANK_DIAMETER] = "invalid_diameter"
            else:
                # Create unique ID based on source entity
                await self.async_set_unique_id(user_input[CONF_SOURCE_ENTITY])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_TANK_DIAMETER): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TankVolumeOptionsFlowHandler:
        """Get the options flow for this handler."""
        return TankVolumeOptionsFlowHandler(config_entry)


class TankVolumeOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Tank Volume Calculator options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            # Validate tank diameter
            if user_input[CONF_TANK_DIAMETER] <= 0:
                errors[CONF_TANK_DIAMETER] = "invalid_diameter"
            else:
                return self.async_create_entry(title="", data=user_input)

        # Get current value from config entry data or options
        current_diameter = self.config_entry.options.get(
            CONF_TANK_DIAMETER,
            self.config_entry.data.get(CONF_TANK_DIAMETER, 24.0),
        )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_TANK_DIAMETER, default=current_diameter
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
