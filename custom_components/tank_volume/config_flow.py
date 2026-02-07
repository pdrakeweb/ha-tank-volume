"""Config flow for Tank Volume Calculator integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    CONF_SOURCE_ENTITY,
    CONF_TANK_DIAMETER,
    DEFAULT_NAME,
    DOMAIN,
)

config_entries.ConfigFlowResult


class TankVolumeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tank Volume Calculator."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate diameter
            diameter = user_input.get(CONF_TANK_DIAMETER, 0)
            if diameter <= 0:
                errors[CONF_TANK_DIAMETER] = "invalid_diameter"
            else:
                # Create entry
                await self.async_set_unique_id(
                    f"{user_input[CONF_SOURCE_ENTITY]}_{user_input[CONF_NAME]}"
                )
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
                vol.Required(CONF_TANK_DIAMETER): vol.All(
                    vol.Coerce(float), vol.Range(min=0, min_included=False)
                ),
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
    ) -> TankVolumeOptionsFlow:
        """Get the options flow for this handler."""
        return TankVolumeOptionsFlow(config_entry)


class TankVolumeOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Tank Volume Calculator."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate diameter
            diameter = user_input.get(CONF_TANK_DIAMETER, 0)
            if diameter <= 0:
                errors[CONF_TANK_DIAMETER] = "invalid_diameter"
            else:
                # Update config entry data
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, **user_input},
                )
                return self.async_create_entry(title="", data={})

        # Show form with current values
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_TANK_DIAMETER,
                    default=self.config_entry.data.get(CONF_TANK_DIAMETER),
                ): vol.All(vol.Coerce(float), vol.Range(min=0, min_included=False)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
