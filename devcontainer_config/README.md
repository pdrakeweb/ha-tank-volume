# Devcontainer Testing Configuration

This directory contains configuration files and scripts for testing the Tank Volume Calculator integration in a devcontainer environment with Home Assistant.

## Quick Start

1. Open this repository in a devcontainer (VS Code will prompt you, or use Command Palette: "Reopen in Container")
2. Once the container is ready, run:
   ```bash
   ./devcontainer_config/start_hass.sh
   ```
3. Wait for Home Assistant to start (this may take a minute on first run)
4. Open your browser to http://localhost:8123
5. Complete the onboarding process (create a user account)

## What's Included

### Mock Tank Height Sensor Integration

A custom integration that provides mock sensors for testing tank volume calculations. The sensors:
- Provide height measurements in inches
- Can be configured with initial values
- Can be updated dynamically via Home Assistant services
- Are perfect for testing the tank_volume integration without real hardware

### Example Configuration

The `configuration.yaml` file includes four pre-configured mock sensors:

1. **Propane Tank Height** - 500 gallon tank at ~25% (9.4 inches)
2. **Small Tank Height** - 250 gallon tank at 50% (15.0 inches)
3. **Empty Tank Height** - Empty tank (0.0 inches)
4. **Full Tank Height** - Full 500 gallon tank (37.5 inches)

## Using Mock Sensors

### Changing Sensor Values

You can change sensor values in two ways:

#### 1. Using Home Assistant UI

1. Go to **Developer Tools** → **Services**
2. Select service: `mock_tank_height_sensor.set_value`
3. Fill in the service data:
   ```yaml
   entity_id: sensor.propane_tank_height
   value: 18.75
   ```
4. Click **Call Service**

#### 2. Using Automation or Scripts

Create automations that change the sensor value:

```yaml
automation:
  - alias: "Simulate Tank Filling"
    trigger:
      platform: time_pattern
      minutes: "/1"
    action:
      service: mock_tank_height_sensor.set_value
      data:
        entity_id: sensor.propane_tank_height
        value: >
          {{ states('sensor.propane_tank_height') | float + 0.5 }}
```

## Testing Tank Volume Calculator

Once Home Assistant is running with mock sensors:

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Tank Volume Calculator"
4. Configure a tank using one of the mock sensors:
   - Name: `My Test Tank`
   - Source sensor: `sensor.propane_tank_height`
   - Tank capacity: `500 gallon`
   - Tank diameter: `37.5` (auto-filled)
   - End cap type: `Ellipsoidal (typical)`

5. View the created sensor in the UI to see the calculated volume percentage

6. Use the mock sensor service to change the height and watch the volume update in real-time

## Automated Testing with Varying Values

For automated testing scenarios, you can use the example automations and scripts provided:

```bash
# Copy automations to your config
cp devcontainer_config/automations.yaml ~/.homeassistant/automations.yaml

# Copy scripts to your config (or include in configuration.yaml)
cp devcontainer_config/scripts.yaml ~/.homeassistant/scripts.yaml
```

The example automations include:
- **Simulate Tank Filling**: Gradually increases height every 30 seconds
- **Simulate Tank Draining**: Gradually decreases height every minute
- **Cycle Fill Levels**: Cycles through 0%, 25%, 50%, 75%, 100% fill levels
- **Random Fill Changes**: Sets random heights for stress testing

The example scripts include:
- **Reset All Tanks**: Resets all mock sensors to default values
- **Fill Tank to Percentage**: Helper to set a tank to a specific fill percentage

Enable automations in the Home Assistant UI: **Settings** → **Automations & Scenes** → Enable desired automations

## Common Test Scenarios

### Test 1: Empty to Full Tank

```yaml
# Developer Tools > Services
service: mock_tank_height_sensor.set_value
data:
  entity_id: sensor.propane_tank_height
  value: 0  # Empty

# Then gradually increase:
# value: 9.375   # 25% for 37.5" diameter tank
# value: 18.75   # 50%
# value: 28.125  # 75%
# value: 37.5    # 100% (full)
```

### Test 2: Different Tank Sizes

Configure multiple tank volume sensors using different mock sensors:
- Use `sensor.small_tank_height` with 250 gallon preset
- Use `sensor.propane_tank_height` with 500 gallon preset

### Test 3: Edge Cases

Test boundary conditions:
- Negative values (should clamp to 0%)
- Values above tank diameter (should clamp to 100%)
- Very small values near 0
- Values very close to diameter

## Troubleshooting

### Home Assistant won't start

- Check that port 8123 is not already in use
- Look for errors in the console output
- Verify configuration.yaml syntax

### Mock sensors not appearing

- Check logs: `grep mock_tank_height_sensor ~/.homeassistant/home-assistant.log`
- Verify the custom_components symlinks were created correctly
- Restart Home Assistant

### Tank Volume integration not found

- Ensure the tank_volume custom component is symlinked properly
- Check that both integrations loaded successfully in the logs

## Development Workflow

1. Make changes to the integration code
2. Restart Home Assistant: Press `Ctrl+C` in the terminal, then run `./devcontainer_config/start_hass.sh` again
3. Test your changes using the mock sensors
4. Iterate as needed

## Advanced: Custom Mock Sensors

To create additional mock sensors, add them to your configuration.yaml:

```yaml
sensor:
  - platform: mock_tank_height_sensor
    name: "Custom Test Sensor"
    initial_value: 12.5
```

Then restart Home Assistant to load the new sensor.
