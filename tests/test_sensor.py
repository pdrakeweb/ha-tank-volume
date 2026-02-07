"""Tests for Tank Volume Calculator sensor platform."""
from unittest.mock import patch

import pytest
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tank_volume.const import (
    CONF_NAME,
    CONF_SOURCE_ENTITY,
    CONF_TANK_DIAMETER,
    CONF_END_CAP_TYPE,
    DOMAIN,
    END_CAP_FLAT,
)


async def test_sensor_setup(hass: HomeAssistant) -> None:
    """Test sensor setup."""
    # Create source sensor
    hass.states.async_set("sensor.fill_height", "12.0")

    # Create config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Tank",
        data={
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 24.0,
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.tank_volume.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


async def test_sensor_state_update(hass: HomeAssistant) -> None:
    """Test sensor state updates when source changes."""
    # Set up sensor domain
    assert await async_setup_component(hass, SENSOR_DOMAIN, {})

    # Create source sensor with initial value (half full)
    hass.states.async_set("sensor.fill_height", "12.0")

    # Set up the integration
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Tank",
        data={
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 24.0,
            CONF_END_CAP_TYPE: END_CAP_FLAT,  # Use flat ends for simple testing
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Get the created sensor entity
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 1
    entity = entities[0]

    # Check initial state (12 inches = 50% of 24 inch diameter)
    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.state != STATE_UNKNOWN
    value = float(state.state)
    assert abs(value - 50.0) < 1.0  # Should be approximately 50%

    # Update source sensor to empty
    hass.states.async_set("sensor.fill_height", "0.0")
    await hass.async_block_till_done()

    state = hass.states.get(entity.entity_id)
    assert state is not None
    value = float(state.state)
    assert value == 0.0

    # Update source sensor to full
    hass.states.async_set("sensor.fill_height", "24.0")
    await hass.async_block_till_done()

    state = hass.states.get(entity.entity_id)
    assert state is not None
    value = float(state.state)
    assert abs(value - 100.0) < 0.1


async def test_sensor_unavailable_source(hass: HomeAssistant) -> None:
    """Test sensor handles unavailable source."""
    assert await async_setup_component(hass, SENSOR_DOMAIN, {})

    # Create source sensor with unavailable state
    hass.states.async_set("sensor.fill_height", STATE_UNAVAILABLE)

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Tank",
        data={
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 24.0,
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 1
    entity = entities[0]

    state = hass.states.get(entity.entity_id)
    assert state is not None
    # When source is unavailable, sensor should also be unavailable or unknown
    assert state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, "None")


async def test_sensor_unknown_source(hass: HomeAssistant) -> None:
    """Test sensor handles unknown source."""
    assert await async_setup_component(hass, SENSOR_DOMAIN, {})

    # Create source sensor with unknown state
    hass.states.async_set("sensor.fill_height", STATE_UNKNOWN)

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Tank",
        data={
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 24.0,
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 1
    entity = entities[0]

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, "None")


async def test_sensor_non_numeric_source(hass: HomeAssistant) -> None:
    """Test sensor handles non-numeric source state."""
    assert await async_setup_component(hass, SENSOR_DOMAIN, {})

    # Create source sensor with non-numeric state
    hass.states.async_set("sensor.fill_height", "not_a_number")

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Tank",
        data={
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 24.0,
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 1
    entity = entities[0]

    state = hass.states.get(entity.entity_id)
    assert state is not None
    # Should be unavailable or None when source is non-numeric
    assert state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, "None")


async def test_sensor_attributes(hass: HomeAssistant) -> None:
    """Test sensor exposes correct attributes."""
    assert await async_setup_component(hass, SENSOR_DOMAIN, {})

    hass.states.async_set("sensor.fill_height", "12.0")

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Tank",
        data={
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 24.0,
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 1
    entity = entities[0]

    state = hass.states.get(entity.entity_id)
    assert state is not None
    assert "source_entity" in state.attributes
    assert state.attributes["source_entity"] == "sensor.fill_height"
    assert "tank_diameter_inches" in state.attributes
    assert state.attributes["tank_diameter_inches"] == 24.0
    assert "fill_height_inches" in state.attributes
    assert state.attributes["fill_height_inches"] == 12.0
