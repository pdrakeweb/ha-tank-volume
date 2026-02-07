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
    CAPACITY_1000,
    CAPACITY_250,
    CAPACITY_330,
    CAPACITY_500,
    CAPACITY_CUSTOM,
    CONF_CYLINDER_LENGTH,
    CONF_END_CAP_TYPE,
    CONF_SOURCE_ENTITY,
    CONF_TANK_CAPACITY,
    CONF_TANK_DIAMETER,
    DEFAULT_END_CAP_TYPE,
    DEFAULT_NAME,
    DEFAULT_TANK_CAPACITY,
    DOMAIN,
    END_CAP_ELLIPSOIDAL_2_1,
    END_CAP_FLAT,
    TANK_SPECS,
)


def calculate_cylinder_length(diameter: float, total_length: float, end_cap_type: str) -> float:
    """Calculate cylinder length from total length and end cap type."""
    if end_cap_type == END_CAP_ELLIPSOIDAL_2_1:
        # For 2:1 ellipsoidal, head depth = diameter / 4
        head_depth = diameter / 4.0
        # Cylinder length = total length - 2 * head depth
        return total_length - (2.0 * head_depth)
    else:
        # For flat ends, cylinder length = total length
        return total_length


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
            
            # Calculate cylinder length based on capacity selection
            tank_capacity = user_input.get(CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY)
            end_cap_type = user_input.get(CONF_END_CAP_TYPE, DEFAULT_END_CAP_TYPE)
            
            if tank_capacity == CAPACITY_CUSTOM:
                # For custom, user must provide diameter
                # Estimate total length as 5x diameter (rough approximation)
                # User can adjust via options if needed
                diameter = user_input[CONF_TANK_DIAMETER]
                estimated_total_length = diameter * 5
                cylinder_length = calculate_cylinder_length(
                    diameter, estimated_total_length, end_cap_type
                )
            else:
                # Use standard specs
                specs = TANK_SPECS.get(tank_capacity, TANK_SPECS[DEFAULT_TANK_CAPACITY])
                total_length = specs["total_length"]
                diameter = user_input[CONF_TANK_DIAMETER]
                cylinder_length = calculate_cylinder_length(
                    diameter, total_length, end_cap_type
                )
            
            # Store calculated cylinder length
            user_input[CONF_CYLINDER_LENGTH] = cylinder_length
            
            if not errors:
                # Create unique ID based on source entity
                await self.async_set_unique_id(user_input[CONF_SOURCE_ENTITY])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        # Determine default diameter based on capacity
        if user_input and CONF_TANK_CAPACITY in user_input:
            capacity = user_input[CONF_TANK_CAPACITY]
            if capacity != CAPACITY_CUSTOM:
                default_diameter = TANK_SPECS[capacity]["diameter"]
            else:
                default_diameter = user_input.get(CONF_TANK_DIAMETER, 37.5)
            default_capacity = capacity
        else:
            default_capacity = DEFAULT_TANK_CAPACITY
            default_diameter = TANK_SPECS[default_capacity]["diameter"]

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_TANK_CAPACITY, default=default_capacity): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": CAPACITY_250, "label": "250 gallon"},
                            {"value": CAPACITY_330, "label": "330 gallon"},
                            {"value": CAPACITY_500, "label": "500 gallon"},
                            {"value": CAPACITY_1000, "label": "1000 gallon"},
                            {"value": CAPACITY_CUSTOM, "label": "Custom"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_TANK_DIAMETER, default=default_diameter): vol.Coerce(float),
                vol.Optional(CONF_END_CAP_TYPE, default=DEFAULT_END_CAP_TYPE): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": END_CAP_ELLIPSOIDAL_2_1, "label": "Ellipsoidal (typical)"},
                            {"value": END_CAP_FLAT, "label": "Flat"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
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
            
            # Calculate cylinder length based on capacity selection
            tank_capacity = user_input.get(CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY)
            end_cap_type = user_input.get(CONF_END_CAP_TYPE, DEFAULT_END_CAP_TYPE)
            
            if tank_capacity == CAPACITY_CUSTOM:
                # For custom, estimate total length
                diameter = user_input[CONF_TANK_DIAMETER]
                estimated_total_length = diameter * 5
                cylinder_length = calculate_cylinder_length(
                    diameter, estimated_total_length, end_cap_type
                )
            else:
                # Use standard specs
                specs = TANK_SPECS.get(tank_capacity, TANK_SPECS[DEFAULT_TANK_CAPACITY])
                total_length = specs["total_length"]
                diameter = user_input[CONF_TANK_DIAMETER]
                cylinder_length = calculate_cylinder_length(
                    diameter, total_length, end_cap_type
                )
            
            # Store calculated cylinder length
            user_input[CONF_CYLINDER_LENGTH] = cylinder_length
            
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        # Get current values from config entry data or options
        current_capacity = self.config_entry.options.get(
            CONF_TANK_CAPACITY,
            self.config_entry.data.get(CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY),
        )
        current_diameter = self.config_entry.options.get(
            CONF_TANK_DIAMETER,
            self.config_entry.data.get(CONF_TANK_DIAMETER, 37.5),
        )
        current_end_cap_type = self.config_entry.options.get(
            CONF_END_CAP_TYPE,
            self.config_entry.data.get(CONF_END_CAP_TYPE, DEFAULT_END_CAP_TYPE),
        )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_TANK_CAPACITY, default=current_capacity
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": CAPACITY_250, "label": "250 gallon"},
                            {"value": CAPACITY_330, "label": "330 gallon"},
                            {"value": CAPACITY_500, "label": "500 gallon"},
                            {"value": CAPACITY_1000, "label": "1000 gallon"},
                            {"value": CAPACITY_CUSTOM, "label": "Custom"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_TANK_DIAMETER, default=current_diameter
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_END_CAP_TYPE, default=current_end_cap_type
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": END_CAP_ELLIPSOIDAL_2_1, "label": "Ellipsoidal (typical)"},
                            {"value": END_CAP_FLAT, "label": "Flat"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
