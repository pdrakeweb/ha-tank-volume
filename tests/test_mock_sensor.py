"""Tests for Mock Tank Height Sensor integration."""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.mock_tank_height_sensor.sensor import MockTankHeightSensor


def test_mock_sensor_creation():
    """Test creating a mock sensor."""
    sensor = MockTankHeightSensor("Test Sensor", 15.5)
    
    assert sensor.name == "Test Sensor"
    assert sensor.native_value == 15.5
    assert sensor.native_unit_of_measurement == "in"
    assert sensor.device_class == "distance"
    assert sensor.state_class == "measurement"
    assert sensor.icon == "mdi:ruler"


def test_mock_sensor_attributes():
    """Test mock sensor attributes."""
    sensor = MockTankHeightSensor("Tank Height", 20.0)
    
    attrs = sensor.extra_state_attributes
    assert "description" in attrs
    assert "editable" in attrs
    assert attrs["editable"] is True


async def test_mock_sensor_platform_setup(hass: HomeAssistant):
    """Test setting up the mock sensor platform."""
    config = {
        "sensor": [
            {
                "platform": "mock_tank_height_sensor",
                "name": "Test Mock Height",
                "initial_value": 12.5,
            }
        ]
    }
    
    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()
    
    # Check that sensor was created
    state = hass.states.get("sensor.test_mock_height")
    assert state is not None
    # Home Assistant may convert units based on system settings
    # Just verify the sensor exists and has a numeric value
    assert state.state is not None
    assert float(state.state) > 0  # Should have some value
    assert state.attributes.get("device_class") == "distance"


async def test_mock_sensor_default_values(hass: HomeAssistant):
    """Test mock sensor with default values."""
    config = {
        "sensor": [
            {
                "platform": "mock_tank_height_sensor",
            }
        ]
    }
    
    assert await async_setup_component(hass, "sensor", config)
    await hass.async_block_till_done()
    
    # Check that sensor was created with defaults
    state = hass.states.get("sensor.mock_tank_height")
    assert state is not None
    assert float(state.state) == 0.0


async def test_mock_sensor_service_setup(hass: HomeAssistant):
    """Test that services are registered."""
    config = {"mock_tank_height_sensor": {}}
    
    assert await async_setup_component(hass, "mock_tank_height_sensor", config)
    await hass.async_block_till_done()
    
    # Check that service is registered
    assert hass.services.has_service("mock_tank_height_sensor", "set_value")
