"""Tests for Tank Volume Calculator config flow."""

from typing import Any
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry
import voluptuous as vol

from custom_components.tank_volume.const import (
    CAPACITY_500,
    CAPACITY_CUSTOM,
    CONF_CYLINDER_LENGTH,
    CONF_END_CAP_TYPE,
    CONF_NAME,
    CONF_SOURCE_ENTITY,
    CONF_TANK_CAPACITY,
    CONF_TANK_DIAMETER,
    CONF_TANK_TOTAL_LENGTH,
    CONF_TANK_VOLUME,
    DOMAIN,
)
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.tank_volume.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test Tank",
                CONF_SOURCE_ENTITY: "sensor.fill_height",
                CONF_TANK_CAPACITY: CAPACITY_CUSTOM,
            },
        )
        await hass.async_block_till_done()

        assert result2["type"] == FlowResultType.FORM
        assert result2["step_id"] == "details"

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_TANK_DIAMETER: 24.0,
                CONF_TANK_TOTAL_LENGTH: 120.0,
                CONF_TANK_VOLUME: 250.0,
            },
        )
        await hass.async_block_till_done()

        assert result3["type"] == FlowResultType.CREATE_ENTRY
        assert result3["title"] == "Test Tank"
        # Verify the essential fields
        assert result3["data"][CONF_NAME] == "Test Tank"
        assert result3["data"][CONF_SOURCE_ENTITY] == "sensor.fill_height"
        assert result3["data"][CONF_TANK_DIAMETER] == 24.0
        # Verify the auto-calculated fields are present
        assert CONF_CYLINDER_LENGTH in result3["data"]
        assert CONF_END_CAP_TYPE in result3["data"]
        assert CONF_TANK_CAPACITY in result3["data"]
        assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_diameter_zero(hass: HomeAssistant) -> None:
    """Test we handle invalid diameter (zero)."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_CAPACITY: CAPACITY_CUSTOM,
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "details"

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            CONF_TANK_DIAMETER: 0.0,
            CONF_TANK_TOTAL_LENGTH: 120.0,
            CONF_TANK_VOLUME: 250.0,
        },
    )

    assert result3["type"] == FlowResultType.FORM
    assert result3["errors"] == {CONF_TANK_DIAMETER: "invalid_diameter"}


async def test_form_invalid_diameter_negative(hass: HomeAssistant) -> None:
    """Test we handle invalid diameter (negative)."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_CAPACITY: CAPACITY_CUSTOM,
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "details"

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            CONF_TANK_DIAMETER: -24.0,
            CONF_TANK_TOTAL_LENGTH: 120.0,
            CONF_TANK_VOLUME: 250.0,
        },
    )

    assert result3["type"] == FlowResultType.FORM
    assert result3["errors"] == {CONF_TANK_DIAMETER: "invalid_diameter"}


async def test_form_duplicate_source_entity(hass: HomeAssistant) -> None:
    """Test we handle duplicate source entity."""
    # Create first entry
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    with patch(
        "custom_components.tank_volume.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test Tank",
                CONF_SOURCE_ENTITY: "sensor.fill_height",
                CONF_TANK_CAPACITY: CAPACITY_CUSTOM,
            },
        )
        await hass.async_block_till_done()

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_TANK_DIAMETER: 24.0,
                CONF_TANK_TOTAL_LENGTH: 120.0,
                CONF_TANK_VOLUME: 250.0,
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] == FlowResultType.CREATE_ENTRY

    # Try to create second entry with same source entity
    result3 = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {
            CONF_NAME: "Test Tank 2",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_CAPACITY: CAPACITY_CUSTOM,
        },
    )

    assert result4["type"] == FlowResultType.FORM
    assert result4["step_id"] == "details"

    result5 = await hass.config_entries.flow.async_configure(
        result4["flow_id"],
        {
            CONF_TANK_DIAMETER: 36.0,
            CONF_TANK_TOTAL_LENGTH: 120.0,
            CONF_TANK_VOLUME: 250.0,
        },
    )

    assert result5["type"] == FlowResultType.ABORT
    assert result5["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow."""
    # Create a config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Tank",
        data={
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 24.0,
        },
        options={},
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    # Initialize options flow
    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Configure options
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_TANK_CAPACITY: CAPACITY_CUSTOM,
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "details"

    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={
            CONF_TANK_DIAMETER: 36.0,
            CONF_TANK_TOTAL_LENGTH: 120.0,
            CONF_TANK_VOLUME: 250.0,
        },
    )

    assert result3["type"] == FlowResultType.CREATE_ENTRY
    # Verify the essential field
    assert result3["data"][CONF_TANK_DIAMETER] == 36.0
    # Verify the auto-calculated fields are present
    assert CONF_CYLINDER_LENGTH in result3["data"]
    assert CONF_END_CAP_TYPE in result3["data"]
    assert CONF_TANK_CAPACITY in result3["data"]


async def test_options_flow_invalid_diameter(hass: HomeAssistant) -> None:
    """Test options flow with invalid diameter."""
    # Create a config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Tank",
        data={
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 24.0,
        },
        options={},
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    # Initialize options flow
    result = await hass.config_entries.options.async_init(entry.entry_id)

    # Configure with invalid diameter
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_TANK_CAPACITY: CAPACITY_CUSTOM,
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "details"

    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={
            CONF_TANK_DIAMETER: -10.0,
            CONF_TANK_TOTAL_LENGTH: 120.0,
            CONF_TANK_VOLUME: 250.0,
        },
    )

    assert result3["type"] == FlowResultType.FORM
    assert result3["errors"] == {CONF_TANK_DIAMETER: "invalid_diameter"}


def _get_schema_default(schema: vol.Schema, key: str) -> float | None:
    for marker in schema.schema:
        if isinstance(marker, vol.Marker) and marker.schema == key:
            default_value = marker.default
            for _ in range(3):
                if callable(default_value):
                    default_value = default_value()
                    continue
                break
            return default_value
    return None


def _get_schema_selector(schema: vol.Schema, key: str) -> Any | None:
    for marker, value in schema.schema.items():
        if isinstance(marker, vol.Marker) and marker.schema == key:
            return value
    return None


def _get_selector_read_only(value: Any) -> bool | None:
    if value is None:
        return None
    if hasattr(value, "config"):
        if isinstance(value.config, dict):
            return value.config.get("read_only")
        return value.config.read_only
    if isinstance(value, dict):
        number_config = value.get("number")
        if isinstance(number_config, dict):
            return number_config.get("read_only")
    return None


async def test_options_flow_prefills_custom_details(hass: HomeAssistant) -> None:
    """Test options flow prefills custom details when reconfiguring."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Tank",
        data={
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_CAPACITY: CAPACITY_CUSTOM,
            CONF_TANK_DIAMETER: 24.0,
            CONF_TANK_TOTAL_LENGTH: 120.0,
            CONF_TANK_VOLUME: 250.0,
        },
        options={},
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_TANK_CAPACITY: CAPACITY_CUSTOM,
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "details"

    schema = result2["data_schema"]
    assert _get_schema_default(schema, CONF_TANK_DIAMETER) == 24.0
    assert _get_schema_default(schema, CONF_TANK_TOTAL_LENGTH) == 120.0
    assert _get_schema_default(schema, CONF_TANK_VOLUME) == 250.0


async def test_options_flow_preset_overrides_details(hass: HomeAssistant) -> None:
    """Test options flow uses preset defaults and locks fields."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Tank",
        data={
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_CAPACITY: CAPACITY_CUSTOM,
            CONF_TANK_DIAMETER: 24.0,
            CONF_TANK_TOTAL_LENGTH: 120.0,
            CONF_TANK_VOLUME: 250.0,
        },
        options={},
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_TANK_CAPACITY: CAPACITY_500,
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "details"

    schema = result2["data_schema"]
    assert _get_schema_default(schema, CONF_TANK_DIAMETER) == 37.5
    assert _get_schema_default(schema, CONF_TANK_TOTAL_LENGTH) == 120.0
    assert _get_schema_default(schema, CONF_TANK_VOLUME) == 500.0

    diameter_selector = _get_schema_selector(schema, CONF_TANK_DIAMETER)
    assert diameter_selector is not None
    assert _get_selector_read_only(diameter_selector) is True
