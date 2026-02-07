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
    CONF_CYLINDER_LENGTH,
    CONF_END_CAP_DEPTH,
    CONF_END_CAP_TYPE,
    CONF_SOURCE_ENTITY,
    CONF_TANK_DIAMETER,
    DEFAULT_END_CAP_TYPE,
    DEFAULT_NAME,
    DOMAIN,
    END_CAP_ELLIPSOIDAL_2_1,
    END_CAP_ELLIPSOIDAL_CUSTOM,
    END_CAP_FLAT,
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
            
            # Validate end cap configuration
            end_cap_type = user_input.get(CONF_END_CAP_TYPE, DEFAULT_END_CAP_TYPE)
            
            if end_cap_type in (END_CAP_ELLIPSOIDAL_2_1, END_CAP_ELLIPSOIDAL_CUSTOM):
                # Validate cylinder length is required for end caps
                cylinder_length = user_input.get(CONF_CYLINDER_LENGTH)
                if not cylinder_length or cylinder_length <= 0:
                    errors[CONF_CYLINDER_LENGTH] = "invalid_cylinder_length"
                
                # Validate custom end cap depth
                if end_cap_type == END_CAP_ELLIPSOIDAL_CUSTOM:
                    end_cap_depth = user_input.get(CONF_END_CAP_DEPTH)
                    if not end_cap_depth or end_cap_depth <= 0:
                        errors[CONF_END_CAP_DEPTH] = "invalid_end_cap_depth"
            
            if not errors:
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
                vol.Optional(CONF_END_CAP_TYPE, default=DEFAULT_END_CAP_TYPE): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": END_CAP_FLAT, "label": "Flat (pure cylinder)"},
                            {"value": END_CAP_ELLIPSOIDAL_2_1, "label": "2:1 Ellipsoidal"},
                            {"value": END_CAP_ELLIPSOIDAL_CUSTOM, "label": "Custom Ellipsoidal"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_CYLINDER_LENGTH): vol.Coerce(float),
                vol.Optional(CONF_END_CAP_DEPTH): vol.Coerce(float),
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
            
            # Validate end cap configuration
            end_cap_type = user_input.get(CONF_END_CAP_TYPE, DEFAULT_END_CAP_TYPE)
            
            if end_cap_type in (END_CAP_ELLIPSOIDAL_2_1, END_CAP_ELLIPSOIDAL_CUSTOM):
                # Validate cylinder length is required for end caps
                cylinder_length = user_input.get(CONF_CYLINDER_LENGTH)
                if not cylinder_length or cylinder_length <= 0:
                    errors[CONF_CYLINDER_LENGTH] = "invalid_cylinder_length"
                
                # Validate custom end cap depth
                if end_cap_type == END_CAP_ELLIPSOIDAL_CUSTOM:
                    end_cap_depth = user_input.get(CONF_END_CAP_DEPTH)
                    if not end_cap_depth or end_cap_depth <= 0:
                        errors[CONF_END_CAP_DEPTH] = "invalid_end_cap_depth"
            
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        # Get current values from config entry data or options
        current_diameter = self.config_entry.options.get(
            CONF_TANK_DIAMETER,
            self.config_entry.data.get(CONF_TANK_DIAMETER, 24.0),
        )
        current_end_cap_type = self.config_entry.options.get(
            CONF_END_CAP_TYPE,
            self.config_entry.data.get(CONF_END_CAP_TYPE, DEFAULT_END_CAP_TYPE),
        )
        current_cylinder_length = self.config_entry.options.get(
            CONF_CYLINDER_LENGTH,
            self.config_entry.data.get(CONF_CYLINDER_LENGTH),
        )
        current_end_cap_depth = self.config_entry.options.get(
            CONF_END_CAP_DEPTH,
            self.config_entry.data.get(CONF_END_CAP_DEPTH),
        )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_TANK_DIAMETER, default=current_diameter
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_END_CAP_TYPE, default=current_end_cap_type
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": END_CAP_FLAT, "label": "Flat (pure cylinder)"},
                            {"value": END_CAP_ELLIPSOIDAL_2_1, "label": "2:1 Ellipsoidal"},
                            {"value": END_CAP_ELLIPSOIDAL_CUSTOM, "label": "Custom Ellipsoidal"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_CYLINDER_LENGTH, default=current_cylinder_length
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_END_CAP_DEPTH, default=current_end_cap_depth
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
