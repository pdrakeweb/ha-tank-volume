"""Tests for Tank Volume Calculator config flow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tank_volume.const import (
    CONF_CYLINDER_LENGTH,
    CONF_END_CAP_TYPE,
    CONF_NAME,
    CONF_SOURCE_ENTITY,
    CONF_TANK_CAPACITY,
    CONF_TANK_DIAMETER,
    CONF_TEMPERATURE_ENTITY,
    DEFAULT_NAME,
    DOMAIN,
)


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
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
                CONF_TANK_DIAMETER: 24.0,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test Tank"
    # Verify the essential fields
    assert result2["data"][CONF_NAME] == "Test Tank"
    assert result2["data"][CONF_SOURCE_ENTITY] == "sensor.fill_height"
    assert result2["data"][CONF_TANK_DIAMETER] == 24.0
    # Verify the auto-calculated fields are present
    assert CONF_CYLINDER_LENGTH in result2["data"]
    assert CONF_END_CAP_TYPE in result2["data"]
    assert CONF_TANK_CAPACITY in result2["data"]
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_diameter_zero(hass: HomeAssistant) -> None:
    """Test we handle invalid diameter (zero)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 0.0,
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {CONF_TANK_DIAMETER: "invalid_diameter"}


async def test_form_invalid_diameter_negative(hass: HomeAssistant) -> None:
    """Test we handle invalid diameter (negative)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: -24.0,
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {CONF_TANK_DIAMETER: "invalid_diameter"}


async def test_form_duplicate_source_entity(hass: HomeAssistant) -> None:
    """Test we handle duplicate source entity."""
    # Create first entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.tank_volume.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test Tank",
                CONF_SOURCE_ENTITY: "sensor.fill_height",
                CONF_TANK_DIAMETER: 24.0,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY

    # Try to create second entry with same source entity
    result3 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {
            CONF_NAME: "Test Tank 2",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 36.0,
        },
    )

    assert result4["type"] == FlowResultType.ABORT
    assert result4["reason"] == "already_configured"


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
        user_input={CONF_TANK_DIAMETER: 36.0},
    )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    # Verify the essential field
    assert result2["data"][CONF_TANK_DIAMETER] == 36.0
    # Verify the auto-calculated fields are present  
    assert CONF_CYLINDER_LENGTH in result2["data"]
    assert CONF_END_CAP_TYPE in result2["data"]
    assert CONF_TANK_CAPACITY in result2["data"]


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
        user_input={CONF_TANK_DIAMETER: -10.0},
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {CONF_TANK_DIAMETER: "invalid_diameter"}


async def test_form_with_temperature_entity(hass: HomeAssistant) -> None:
    """Test we can configure with a temperature entity."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
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
                CONF_TANK_DIAMETER: 37.5,
                CONF_TEMPERATURE_ENTITY: "sensor.tank_temperature",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test Tank"
    assert result2["data"][CONF_NAME] == "Test Tank"
    assert result2["data"][CONF_SOURCE_ENTITY] == "sensor.fill_height"
    assert result2["data"][CONF_TANK_DIAMETER] == 37.5
    assert result2["data"][CONF_TEMPERATURE_ENTITY] == "sensor.tank_temperature"
    assert len(mock_setup_entry.mock_calls) == 1


async def test_options_flow_with_temperature_entity(hass: HomeAssistant) -> None:
    """Test options flow with temperature entity."""
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
        source=config_entries.SOURCE_USER,
        unique_id="sensor.fill_height",
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)

    # Initialize options flow
    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Configure options with temperature entity
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_TANK_DIAMETER: 36.0,
            CONF_TEMPERATURE_ENTITY: "sensor.propane_temperature",
        },
    )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_TANK_DIAMETER] == 36.0
    assert result2["data"][CONF_TEMPERATURE_ENTITY] == "sensor.propane_temperature"

