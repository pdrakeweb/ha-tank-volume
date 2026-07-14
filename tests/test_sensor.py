"""Tests for Tank Volume Calculator sensor platform."""

from datetime import timedelta
from unittest.mock import patch

from freezegun import freeze_time
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tank_volume.const import (
    CONF_ADJUSTMENT_COEFFICIENT,
    CONF_END_CAP_TYPE,
    CONF_NAME,
    CONF_SOURCE_ENTITY,
    CONF_TANK_DIAMETER,
    CONF_TANK_VOLUME,
    CONF_TEMPERATURE_ENTITY,
    CONF_TEMPERATURE_LAG_HOURS,
    CONF_TEMPERATURE_LAG_PER_DEGREE,
    CONF_TEMPERATURE_SMOOTHING_HOURS,
    DEFAULT_ADJUSTMENT_COEFFICIENT,
    DOMAIN,
    END_CAP_FLAT,
)
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util


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
            CONF_TANK_VOLUME: 250.0,
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
    assert len(entities) == 2
    fill_level_entity = next(entity for entity in entities if entity.unique_id.endswith("_fill_level"))
    contents_entity = next(entity for entity in entities if entity.unique_id.endswith("_contents_volume"))

    # Check initial state (12 inches = 50% of 24 inch diameter)
    state = hass.states.get(fill_level_entity.entity_id)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.state != STATE_UNKNOWN
    value = float(state.state)
    assert abs(value - 50.0) < 1.0  # Should be approximately 50%

    contents_state = hass.states.get(contents_entity.entity_id)
    assert contents_state is not None
    contents_value = float(contents_state.state)
    assert abs(contents_value - 125.0) < 1.0

    # Update source sensor to empty
    hass.states.async_set("sensor.fill_height", "0.0")
    await hass.async_block_till_done()

    state = hass.states.get(fill_level_entity.entity_id)
    assert state is not None
    value = float(state.state)
    assert value == 0.0

    contents_state = hass.states.get(contents_entity.entity_id)
    assert contents_state is not None
    contents_value = float(contents_state.state)
    assert contents_value == 0.0

    # Update source sensor to full
    hass.states.async_set("sensor.fill_height", "24.0")
    await hass.async_block_till_done()

    state = hass.states.get(fill_level_entity.entity_id)
    assert state is not None
    value = float(state.state)
    assert abs(value - 100.0) < 0.1

    contents_state = hass.states.get(contents_entity.entity_id)
    assert contents_state is not None
    contents_value = float(contents_state.state)
    assert abs(contents_value - 250.0) < 0.1


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
            CONF_TANK_VOLUME: 250.0,
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 2

    for entity in entities:
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
            CONF_TANK_VOLUME: 250.0,
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 2

    for entity in entities:
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
            CONF_TANK_VOLUME: 250.0,
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 2

    for entity in entities:
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
            CONF_TANK_VOLUME: 250.0,
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 2
    fill_level_entity = next(entity for entity in entities if entity.unique_id.endswith("_fill_level"))

    state = hass.states.get(fill_level_entity.entity_id)
    assert state is not None
    assert "source_entity" in state.attributes
    assert state.attributes["source_entity"] == "sensor.fill_height"
    assert "tank_diameter_inches" in state.attributes
    assert state.attributes["tank_diameter_inches"] == 24.0
    assert "fill_height_inches" in state.attributes
    assert state.attributes["fill_height_inches"] == 12.0
    assert "adjustment_coefficient" in state.attributes
    assert state.attributes["adjustment_coefficient"] == DEFAULT_ADJUSTMENT_COEFFICIENT


async def test_sensor_temperature_compensation_fahrenheit(hass: HomeAssistant) -> None:
    """Test sensor applies temperature compensation for Fahrenheit."""
    assert await async_setup_component(hass, SENSOR_DOMAIN, {})

    hass.states.async_set("sensor.fill_height", "12.0")
    hass.states.async_set(
        "sensor.lp_temp",
        "80.0",
        {"unit_of_measurement": UnitOfTemperature.FAHRENHEIT},
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Tank",
        data={
            CONF_NAME: "Test Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 24.0,
            CONF_TEMPERATURE_ENTITY: "sensor.lp_temp",
            CONF_END_CAP_TYPE: END_CAP_FLAT,
            CONF_TANK_VOLUME: 250.0,
            CONF_ADJUSTMENT_COEFFICIENT: 0.003,
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 4

    base_entity = next(entity for entity in entities if entity.unique_id.endswith("_fill_level"))
    adjusted_entity = next(
        entity for entity in entities if entity.unique_id.endswith("_temperature_adjusted_fill_level")
    )

    base_state = hass.states.get(base_entity.entity_id)
    assert base_state is not None
    base_value = float(base_state.state)
    assert abs(base_value - 50.0) < 0.1

    adjusted_state = hass.states.get(adjusted_entity.entity_id)
    assert adjusted_state is not None
    adjusted_value = float(adjusted_state.state)

    assert abs(adjusted_value - (50.0 / 1.06)) < 0.1


async def _adjusted_fill_value(hass: HomeAssistant, entry: MockConfigEntry) -> float:
    """Return the current temperature-adjusted fill-level value for an entry."""
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    adjusted_entity = next(
        entity for entity in entities if entity.unique_id.endswith("_temperature_adjusted_fill_level")
    )
    state = hass.states.get(adjusted_entity.entity_id)
    assert state is not None
    return float(state.state)


async def test_sensor_temperature_lag_uses_delayed_reading(hass: HomeAssistant) -> None:
    """A configured lag compensates against the delayed (bulk) temperature, not the latest reading."""
    assert await async_setup_component(hass, SENSOR_DOMAIN, {})

    start = dt_util.utcnow().replace(microsecond=0)
    with freeze_time(start) as frozen:
        hass.states.async_set("sensor.fill_height", "12.0")  # 50% at diameter 24
        hass.states.async_set(
            "sensor.lp_temp",
            "60.0",  # reference temperature -> no adjustment initially
            {"unit_of_measurement": UnitOfTemperature.FAHRENHEIT},
        )

        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Lag Tank",
            data={
                CONF_NAME: "Lag Tank",
                CONF_SOURCE_ENTITY: "sensor.fill_height",
                CONF_TANK_DIAMETER: 24.0,
                CONF_TEMPERATURE_ENTITY: "sensor.lp_temp",
                CONF_END_CAP_TYPE: END_CAP_FLAT,
                CONF_TANK_VOLUME: 250.0,
                CONF_ADJUSTMENT_COEFFICIENT: 0.003,
                CONF_TEMPERATURE_LAG_HOURS: 1.0,
                CONF_TEMPERATURE_LAG_PER_DEGREE: 0.0,  # pin a constant 1 h lag for a deterministic check
                CONF_TEMPERATURE_SMOOTHING_HOURS: 0.0,
            },
            unique_id="sensor.fill_height",
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Two hours later the sensor reports 100 F, but the bulk temperature one hour
        # ago (the lag target) is halfway between 60 and 100 -> 80 F.
        frozen.move_to(start + timedelta(hours=2))
        hass.states.async_set(
            "sensor.lp_temp",
            "100.0",
            {"unit_of_measurement": UnitOfTemperature.FAHRENHEIT},
        )
        await hass.async_block_till_done()

        adjusted = await _adjusted_fill_value(hass, entry)

    # Compensation should use ~80 F (delayed), i.e. 50 / (1 + 0.003 * 20) = 50 / 1.06 ...
    assert abs(adjusted - (50.0 / 1.06)) < 0.3
    # ... and NOT the instantaneous 100 F, which would give 50 / 1.12.
    assert abs(adjusted - (50.0 / 1.12)) > 0.3


async def test_sensor_temperature_lag_zero_uses_instantaneous(hass: HomeAssistant) -> None:
    """Lag 0 disables the estimator and reproduces instantaneous compensation."""
    assert await async_setup_component(hass, SENSOR_DOMAIN, {})

    hass.states.async_set("sensor.fill_height", "12.0")
    hass.states.async_set(
        "sensor.lp_temp",
        "80.0",
        {"unit_of_measurement": UnitOfTemperature.FAHRENHEIT},
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="No Lag Tank",
        data={
            CONF_NAME: "No Lag Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 24.0,
            CONF_TEMPERATURE_ENTITY: "sensor.lp_temp",
            CONF_END_CAP_TYPE: END_CAP_FLAT,
            CONF_TANK_VOLUME: 250.0,
            CONF_ADJUSTMENT_COEFFICIENT: 0.003,
            CONF_TEMPERATURE_LAG_HOURS: 0.0,
            CONF_TEMPERATURE_LAG_PER_DEGREE: 0.0,  # both zero -> estimator disabled (instantaneous)
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    adjusted_entity = next(
        entity for entity in entities if entity.unique_id.endswith("_temperature_adjusted_fill_level")
    )
    state = hass.states.get(adjusted_entity.entity_id)
    assert state is not None
    # 80 F instantaneous -> 50 / (1 + 0.003 * 20) = 50 / 1.06.
    assert abs(float(state.state) - (50.0 / 1.06)) < 0.1
    # Estimator disabled -> no lag diagnostics on the entity.
    assert "temperature_lag_hours" not in state.attributes


async def test_sensor_temperature_lag_exposes_attributes(hass: HomeAssistant) -> None:
    """With a lag configured, the adjusted sensor exposes lag diagnostics."""
    assert await async_setup_component(hass, SENSOR_DOMAIN, {})

    hass.states.async_set("sensor.fill_height", "12.0")
    hass.states.async_set(
        "sensor.lp_temp",
        "70.0",
        {"unit_of_measurement": UnitOfTemperature.FAHRENHEIT},
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Attr Tank",
        data={
            CONF_NAME: "Attr Tank",
            CONF_SOURCE_ENTITY: "sensor.fill_height",
            CONF_TANK_DIAMETER: 24.0,
            CONF_TEMPERATURE_ENTITY: "sensor.lp_temp",
            CONF_END_CAP_TYPE: END_CAP_FLAT,
            CONF_TANK_VOLUME: 250.0,
            CONF_TEMPERATURE_LAG_HOURS: 6.0,
            CONF_TEMPERATURE_LAG_PER_DEGREE: 0.067,
            CONF_TEMPERATURE_SMOOTHING_HOURS: 1.0,
        },
        unique_id="sensor.fill_height",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    adjusted_entity = next(
        entity for entity in entities if entity.unique_id.endswith("_temperature_adjusted_fill_level")
    )
    state = hass.states.get(adjusted_entity.entity_id)
    assert state is not None
    assert state.attributes["temperature_lag_hours"] == 6.0
    assert state.attributes["temperature_lag_per_degree"] == 0.067
    assert state.attributes["temperature_smoothing_hours"] == 1.0
    assert "bulk_temperature_f" in state.attributes
    # 70 F is 10 F above the 60 F reference -> effective lag ~ 6 + 0.067*10 = 6.67 h.
    assert abs(state.attributes["effective_lag_hours"] - 6.67) < 0.3
