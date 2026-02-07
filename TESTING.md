# Testing Guide

This document describes how to test the Tank Volume Calculator integration, both with automated tests and with a live Home Assistant instance in the devcontainer.

## Automated Testing (pytest)

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=custom_components/tank_volume --cov-report=term-missing -v

# Run specific test file
pytest tests/test_sensor.py -v
pytest tests/test_volume_calculation.py -v
pytest tests/test_mock_sensor.py -v
```

### Test Structure

- **test_volume_calculation.py**: Tests for volume calculation algorithms
- **test_sensor.py**: Tests for the tank_volume sensor entity (some tests may have issues with newer HA versions)
- **test_config_flow.py**: Tests for the configuration flow (some tests may have issues with newer HA versions)
- **test_mock_sensor.py**: Tests for the mock tank height sensor

## Manual Testing with Home Assistant

The repository includes a mock tank height sensor integration designed specifically for testing the tank volume calculator in a live Home Assistant environment.

### Quick Start

1. Open this repository in VS Code with the Dev Containers extension
2. When prompted, reopen in container (or use Command Palette: "Dev Containers: Reopen in Container")
3. Once ready, run:
   ```bash
   ./devcontainer_config/start_hass.sh
   ```
4. Open http://localhost:8123 and complete onboarding
5. Configure the tank volume calculator integration using mock sensors

### Mock Tank Height Sensor

The mock sensor integration provides:
- Configurable initial values in inches
- Service to dynamically change values
- Distance device class (Home Assistant may convert to preferred units)
- Perfect for testing without physical hardware

### Example Workflow

1. **Start Home Assistant** (as shown above)

2. **Add Mock Sensors** (pre-configured in configuration.yaml):
   - `sensor.propane_tank_height` - 9.4 inches
   - `sensor.small_tank_height` - 15.0 inches
   - `sensor.empty_tank_height` - 0.0 inches
   - `sensor.full_tank_height` - 37.5 inches

3. **Configure Tank Volume Calculator**:
   - Go to Settings → Devices & Services → Add Integration
   - Search for "Tank Volume Calculator"
   - Configure with:
     - Name: "My Test Tank"
     - Source: `sensor.propane_tank_height`
     - Capacity: 500 gallon
     - Diameter: 37.5" (auto-filled)
     - End caps: Ellipsoidal (typical)

4. **Test Volume Calculation**:
   - View the tank volume sensor showing percentage
   - Change mock sensor value:
     - Developer Tools → Services
     - Service: `mock_tank_height_sensor.set_value`
     - Data:
       ```yaml
       entity_id: sensor.propane_tank_height
       value: 18.75
       ```
   - Watch volume percentage update in real-time

### Test Scenarios

#### Scenario 1: Empty to Full Tank (500 gallon, 37.5" diameter)

```yaml
# 0% - Empty
service: mock_tank_height_sensor.set_value
data:
  entity_id: sensor.propane_tank_height
  value: 0

# 25% - Quarter full  
value: 9.375

# 50% - Half full
value: 18.75

# 75% - Three quarters full
value: 28.125

# 100% - Full
value: 37.5
```

#### Scenario 2: Different Tank Sizes

Configure multiple tank volume sensors:
- 250 gallon tank (30" diameter) using `sensor.small_tank_height`
- 500 gallon tank (37.5" diameter) using `sensor.propane_tank_height`
- 1000 gallon tank (41" diameter) using a custom mock sensor

#### Scenario 3: Automated Testing with Automations

Copy the example automations:
```bash
cp devcontainer_config/automations.yaml ~/.homeassistant/
```

Enable automations in UI to:
- Simulate gradual tank filling
- Simulate gradual tank draining
- Cycle through preset fill levels
- Random fill changes for stress testing

#### Scenario 4: Edge Cases

Test boundary conditions:
- Negative values (should clamp to 0%)
- Values above diameter (should clamp to 100%)
- Very small increments near 0
- Very small increments near full

### Verification Points

For each test scenario, verify:
1. ✓ Sensor displays reasonable percentage (0-100%)
2. ✓ Volume percentage is NOT linear with height (due to cylinder geometry)
3. ✓ At 50% height, volume is typically < 50% (normal for horizontal cylinders)
4. ✓ Sensor attributes show correct source entity and tank parameters
5. ✓ State updates immediately when source sensor changes
6. ✓ Invalid source states (unavailable, unknown, non-numeric) are handled gracefully

### Expected Behaviors

**For Pure Cylinder (Flat Ends)**:
- 50% height → ~50% volume
- Linear relationship between height and volume percentage

**For Ellipsoidal Heads (Typical LP Tanks)**:
- 50% height → Slightly less than 50% volume
- Non-linear due to ellipsoidal end cap geometry
- More pronounced in smaller diameter tanks

### Common Issues

**Issue**: Sensor shows "Unknown" or "Unavailable"
- **Check**: Source sensor exists and has valid state
- **Check**: Integration is properly configured
- **Fix**: Restart Home Assistant or reconfigure integration

**Issue**: Volume seems incorrect
- **Check**: Tank capacity preset matches your actual tank
- **Check**: Tank diameter is correct
- **Check**: End cap type matches your tank (most LP tanks use ellipsoidal)

**Issue**: Mock sensor value doesn't change
- **Check**: Service call syntax is correct
- **Check**: Entity ID matches exactly
- **Fix**: Check Home Assistant logs for errors

## Linting

```bash
# Check code style
flake8 custom_components/tank_volume/ custom_components/mock_tank_height_sensor/ tests/
```

## Documentation

See also:
- [devcontainer_config/README.md](devcontainer_config/README.md) - Detailed devcontainer testing guide
- [README.md](README.md) - Main integration documentation

## Contributing

When contributing:
1. Run all tests and ensure they pass
2. Add tests for new functionality
3. Test manually in devcontainer when possible
4. Lint your code before submitting
5. Update documentation as needed
