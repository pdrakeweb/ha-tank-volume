"""Config flow for Tank Volume Calculator integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CAPACITY_250,
    CAPACITY_330,
    CAPACITY_500,
    CAPACITY_1000,
    CAPACITY_CUSTOM,
    CONF_CYLINDER_LENGTH,
    CONF_END_CAP_TYPE,
    CONF_SOURCE_ENTITY,
    CONF_TANK_CAPACITY,
    CONF_TANK_DIAMETER,
    CONF_TANK_TOTAL_LENGTH,
    CONF_TANK_VOLUME,
    CONF_TEMPERATURE_ENTITY,
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
    # For flat ends, cylinder length = total length
    return total_length


def _get_details_defaults(
    tank_capacity: str,
    user_input: dict[str, Any] | None = None,
    existing_values: dict[str, Any] | None = None,
) -> dict[str, float | None]:
    defaults: dict[str, float | None]
    if tank_capacity != CAPACITY_CUSTOM:
        specs = TANK_SPECS.get(tank_capacity, TANK_SPECS[DEFAULT_TANK_CAPACITY])
        defaults = {
            CONF_TANK_DIAMETER: specs["diameter"],
            CONF_TANK_TOTAL_LENGTH: specs["total_length"],
            CONF_TANK_VOLUME: float(tank_capacity),
        }
    else:
        defaults = {
            CONF_TANK_DIAMETER: None,
            CONF_TANK_TOTAL_LENGTH: None,
            CONF_TANK_VOLUME: None,
        }

    if existing_values and tank_capacity == CAPACITY_CUSTOM:
        for key in (CONF_TANK_DIAMETER, CONF_TANK_TOTAL_LENGTH, CONF_TANK_VOLUME):
            if key in existing_values and existing_values[key] is not None:
                defaults[key] = existing_values[key]

    if user_input:
        for key in (CONF_TANK_DIAMETER, CONF_TANK_TOTAL_LENGTH, CONF_TANK_VOLUME):
            if key in user_input:
                defaults[key] = user_input[key]

    return defaults


def _build_details_schema(
    diameter_default: float | None,
    total_length_default: float | None,
    volume_default: float | None,
    read_only: bool,
) -> vol.Schema:
    schema_fields: dict[vol.Marker, Any] = {}

    number_selector = selector.NumberSelector(
        selector.NumberSelectorConfig(
            mode=selector.NumberSelectorMode.BOX,
            read_only=read_only,
        )
    )

    if diameter_default is None:
        schema_fields[vol.Required(CONF_TANK_DIAMETER)] = number_selector
    else:
        schema_fields[vol.Required(CONF_TANK_DIAMETER, default=diameter_default)] = number_selector

    if total_length_default is None:
        schema_fields[vol.Required(CONF_TANK_TOTAL_LENGTH)] = number_selector
    else:
        schema_fields[vol.Required(CONF_TANK_TOTAL_LENGTH, default=total_length_default)] = number_selector

    if volume_default is None:
        schema_fields[vol.Required(CONF_TANK_VOLUME)] = number_selector
    else:
        schema_fields[vol.Required(CONF_TANK_VOLUME, default=volume_default)] = number_selector

    return vol.Schema(schema_fields)


class TankVolumeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tank Volume Calculator."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            tank_capacity = user_input.get(CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY)
            user_input[CONF_TANK_CAPACITY] = tank_capacity
            end_cap_type = user_input.get(CONF_END_CAP_TYPE, DEFAULT_END_CAP_TYPE)
            user_input.setdefault(CONF_END_CAP_TYPE, end_cap_type)

            self._user_input = user_input
            return await self.async_step_details()

        default_capacity = DEFAULT_TANK_CAPACITY

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_TEMPERATURE_ENTITY): selector.EntitySelector(
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

    async def async_step_details(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle tank dimension details step."""
        if not hasattr(self, "_user_input"):
            return await self.async_step_user()

        errors: dict[str, str] = {}

        if user_input is not None:
            diameter = user_input[CONF_TANK_DIAMETER]
            total_length = user_input[CONF_TANK_TOTAL_LENGTH]
            tank_volume = user_input[CONF_TANK_VOLUME]

            if diameter <= 0:
                errors[CONF_TANK_DIAMETER] = "invalid_diameter"
            if total_length <= 0:
                errors[CONF_TANK_TOTAL_LENGTH] = "invalid_length"
            if tank_volume <= 0:
                errors[CONF_TANK_VOLUME] = "invalid_volume"

            end_cap_type = self._user_input.get(CONF_END_CAP_TYPE, DEFAULT_END_CAP_TYPE)
            cylinder_length = calculate_cylinder_length(diameter, total_length, end_cap_type)

            if not errors:
                for entry in self._async_current_entries():
                    if entry.data.get(CONF_SOURCE_ENTITY) == self._user_input[CONF_SOURCE_ENTITY]:
                        return self.async_abort(reason="already_configured")

                data = {
                    **self._user_input,
                    **user_input,
                    CONF_CYLINDER_LENGTH: cylinder_length,
                }

                return self.async_create_entry(
                    title=self._user_input[CONF_NAME],
                    data=data,
                )

        tank_capacity = self._user_input.get(CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY)
        defaults = _get_details_defaults(tank_capacity, user_input)
        read_only = tank_capacity != CAPACITY_CUSTOM
        data_schema = _build_details_schema(
            defaults[CONF_TANK_DIAMETER],
            defaults[CONF_TANK_TOTAL_LENGTH],
            defaults[CONF_TANK_VOLUME],
            read_only,
        )

        return self.async_show_form(
            step_id="details",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TankVolumeOptionsFlowHandler:
        """Get the options flow for this handler."""
        return TankVolumeOptionsFlowHandler()


class TankVolumeOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Tank Volume Calculator options."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            tank_capacity = user_input.get(CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY)
            user_input[CONF_TANK_CAPACITY] = tank_capacity
            end_cap_type = user_input.get(CONF_END_CAP_TYPE, DEFAULT_END_CAP_TYPE)
            user_input.setdefault(CONF_END_CAP_TYPE, end_cap_type)

            self._options_input = user_input
            return await self.async_step_details()

        # Get current values from config entry data or options
        current_capacity = self.config_entry.options.get(
            CONF_TANK_CAPACITY,
            self.config_entry.data.get(CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY),
        )
        current_end_cap_type = self.config_entry.options.get(
            CONF_END_CAP_TYPE,
            self.config_entry.data.get(CONF_END_CAP_TYPE, DEFAULT_END_CAP_TYPE),
        )
        current_temperature_entity = self.config_entry.options.get(
            CONF_TEMPERATURE_ENTITY,
            self.config_entry.data.get(CONF_TEMPERATURE_ENTITY),
        )

        temperature_selector: dict[vol.Marker, selector.Selector] = {}
        if current_temperature_entity:
            temperature_selector = {
                vol.Optional(CONF_TEMPERATURE_ENTITY, default=current_temperature_entity): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                )
            }
        else:
            temperature_selector = {
                vol.Optional(CONF_TEMPERATURE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                )
            }

        data_schema = vol.Schema(
            {
                vol.Required(CONF_TANK_CAPACITY, default=current_capacity): selector.SelectSelector(
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
                vol.Optional(CONF_END_CAP_TYPE, default=current_end_cap_type): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": END_CAP_ELLIPSOIDAL_2_1, "label": "Ellipsoidal (typical)"},
                            {"value": END_CAP_FLAT, "label": "Flat"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                **temperature_selector,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_details(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the tank dimension details options step."""
        if not hasattr(self, "_options_input"):
            return await self.async_step_init()

        errors: dict[str, str] = {}

        if user_input is not None:
            diameter = user_input[CONF_TANK_DIAMETER]
            total_length = user_input[CONF_TANK_TOTAL_LENGTH]
            tank_volume = user_input[CONF_TANK_VOLUME]

            if diameter <= 0:
                errors[CONF_TANK_DIAMETER] = "invalid_diameter"
            if total_length <= 0:
                errors[CONF_TANK_TOTAL_LENGTH] = "invalid_length"
            if tank_volume <= 0:
                errors[CONF_TANK_VOLUME] = "invalid_volume"

            end_cap_type = self._options_input.get(CONF_END_CAP_TYPE, DEFAULT_END_CAP_TYPE)
            cylinder_length = calculate_cylinder_length(diameter, total_length, end_cap_type)

            if not errors:
                data = {
                    **self._options_input,
                    **user_input,
                    CONF_CYLINDER_LENGTH: cylinder_length,
                }
                return self.async_create_entry(title="", data=data)

        tank_capacity = self._options_input.get(CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY)
        read_only = tank_capacity != CAPACITY_CUSTOM
        existing_values = {
            CONF_TANK_DIAMETER: self.config_entry.options.get(
                CONF_TANK_DIAMETER,
                self.config_entry.data.get(CONF_TANK_DIAMETER),
            ),
            CONF_TANK_TOTAL_LENGTH: self.config_entry.options.get(
                CONF_TANK_TOTAL_LENGTH,
                self.config_entry.data.get(CONF_TANK_TOTAL_LENGTH),
            ),
            CONF_TANK_VOLUME: self.config_entry.options.get(
                CONF_TANK_VOLUME,
                self.config_entry.data.get(CONF_TANK_VOLUME),
            ),
        }
        defaults = _get_details_defaults(tank_capacity, user_input, existing_values)
        data_schema = _build_details_schema(
            defaults[CONF_TANK_DIAMETER],
            defaults[CONF_TANK_TOTAL_LENGTH],
            defaults[CONF_TANK_VOLUME],
            read_only,
        )

        return self.async_show_form(
            step_id="details",
            data_schema=data_schema,
            errors=errors,
        )
