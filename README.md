# Tank Volume Calculator for Home Assistant

A Home Assistant custom integration that calculates the volumetric fill percentage of horizontal cylindrical tanks with semi-ellipsoidal (dished) end caps - perfect for residential propane (LP) tanks.

## Features

- **Standard LP Tank Presets**: Pre-configured settings for common 250, 330, 500, and 1000 gallon tanks
- **Accurate Volume Calculation**: Converts linear fill height measurements to volumetric fill percentage
- **Ellipsoidal Head Support**: Accounts for standard 2:1 semi-ellipsoidal end caps found on most LP tanks
- **Temperature Compensation**: Automatically adjusts volume readings based on liquid temperature to provide accurate measurements at reference temperature (60°F/15°C)
- **Real-time Updates**: Automatically updates when source sensor changes
- **Easy Configuration**: Simple UI-based setup with smart defaults
- **Flexible Units**: Works with any distance sensor (ultrasonic, pressure, etc.)

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/tank_volume` folder from this repository
2. Copy it to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

### Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Tank Volume Calculator"
4. Fill in the configuration form:
   - **Name**: A friendly name for your tank
   - **Source sensor**: The entity that provides fill height in inches
   - **Temperature sensor** (optional): A temperature sensor entity for temperature compensation
   - **Tank capacity**: Select your tank size:
     - **250 gallon** (30" diameter, 92" total length)
     - **330 gallon** (30" diameter, 120" total length)
     - **500 gallon** (37.5" diameter, 120" total length)
     - **1000 gallon** (41" diameter, 190" total length)
     - **Custom** (specify your own diameter)
   - **Tank diameter**: Auto-filled based on capacity selection (editable)
   - **End cap type**: Choose the geometry of your tank ends:
     - **Ellipsoidal (typical)**: Standard 2:1 semi-ellipsoidal heads (default - most LP tanks)
     - **Flat**: Pure cylinder with no end caps

### Options

You can modify the tank parameters after setup:

1. Go to **Settings** → **Devices & Services**
2. Find the Tank Volume Calculator integration
3. Click **Configure**
4. Update the values as needed

## Standard LP Tank Specifications

Based on common residential propane tank dimensions:

| Capacity | Diameter | Total Length | Cylinder Length* | Head Depth* |
|----------|----------|--------------|------------------|-------------|
| 250 gal  | 30"      | 92"          | 77"              | 7.5"        |
| 330 gal  | 30"      | 120"         | 105"             | 7.5"        |
| 500 gal  | 37.5"    | 120"         | 101.25"          | 9.375"      |
| 1000 gal | 41"      | 190"         | 169.5"           | 10.25"      |

*Calculated automatically for ellipsoidal heads (head depth = diameter ÷ 4)

## Tank Geometry Types

### Ellipsoidal (Typical) - Default

The most common type for residential and commercial LP tanks. These heads have a standard 2:1 elliptical ratio where the depth of each head is exactly 1/4 of the tank diameter.

**Configuration:**
- End cap type: `Ellipsoidal (typical)`
- Cylinder length: Automatically calculated from tank capacity and diameter

**How it works:**
- For a 500 gallon tank (37.5" diameter, 120" total length):
  - Each head depth: 9.375" (37.5 ÷ 4)
  - Cylinder length: 101.25" (120 - 2 × 9.375)
  - Total capacity includes both cylinder and head volumes

**Use when:**
- You have a standard residential LP tank (most common)
- Your tank has rounded/dished ends
- Tank manufacturer specs indicate "2:1 ellipsoidal heads"

### Flat

A simple horizontal cylinder with flat ends.

**Configuration:**
- End cap type: `Flat`
- Works with any diameter

**Use when:**
- Your tank has flat ends (rare for LP tanks)
- You want to measure a section of pipe
- You're using a custom cylindrical tank

## Temperature Compensation

### Why Temperature Compensation Matters

Liquid propane (and other liquids) expand when heated and contract when cooled. This means that the same *mass* of propane occupies different *volumes* at different temperatures. For accurate inventory tracking and billing, volumes are typically standardized to a reference temperature.

### How It Works

When you configure a temperature sensor, the integration automatically compensates for temperature effects using industry-standard volumetric thermal expansion coefficients:

- **For Fahrenheit sensors**: β = 0.00205 per °F (reference: 60°F)
- **For Celsius sensors**: β = 0.00369 per °C (reference: 15°C)

The formula used is:
```
V_reference = V_measured / [1 + β × (T_measured - T_reference)]
```

### Configuration

1. Add a temperature sensor that measures the liquid temperature (not ambient air temperature)
2. Select it in the configuration or options flow
3. The sensor will automatically detect if it's Celsius or Fahrenheit
4. Volume readings will be automatically compensated

### Example

If your tank reads 50% full at 80°F:
- Measured volume: 50%
- Temperature difference: 80°F - 60°F = 20°F
- Compensation factor: 1 / (1 + 0.00205 × 20) ≈ 0.9606
- Compensated volume: 50% × 0.9606 ≈ 48%

This means that if the liquid cooled to the reference temperature (60°F), it would occupy about 48% of the tank.

### Temperature Sensor Requirements

- Must have `device_class: temperature`
- Must provide numeric values
- Must have `unit_of_measurement` set to either `°F` or `°C`
- Should measure liquid temperature, not ambient air (for best accuracy)

**Note**: Temperature compensation is optional. If no temperature sensor is configured, the integration will report volume at the measured temperature.

## Mathematical Background

### Pure Cylinder (Flat Ends)

For a horizontal cylinder with radius `r` and liquid fill height `h`:

The cross-sectional area of liquid is a circular segment:
```
A(h) = r² · arccos((r - h) / r) - (r - h) · √(2rh - h²)
```

Volumetric fill percentage:
```
Fill % = [A(h) / (π · r²)] × 100
```

### Ellipsoidal Heads (2:1 Ratio)

For a semi-ellipsoidal head with radius `r`, head depth `a = r/2`, and fill height `h`:

Volume of liquid in one head:
```
V_head(h) = (π × h² × (3r - h)) / (6 × r)
```

Total tank volume at height `h`:
```
V_total(h) = [Cylinder cross-section × L] + [2 × V_head(h)]
```

Where `L` is the cylinder length (total length minus 2 × head depth).

Total capacity:
```
V_capacity = π × r² × L + 2 × [(2/3) × π × r² × a]
```

Fill percentage:
```
Fill % = [V_total(h) / V_capacity] × 100
```

## Example Configurations

### Example 1: Standard 500 Gallon LP Tank with Temperature Compensation

```yaml
Name: Propane Tank
Source sensor: sensor.propane_ultrasonic_distance
Temperature sensor: sensor.propane_temperature  # Optional but recommended
Tank capacity: 500 gallon
Tank diameter: 37.5  # Auto-filled
End cap type: Ellipsoidal (typical)  # Default
```

The integration automatically calculates:
- Cylinder length: 101.25" (120" total - 2 × 9.375" heads)
- Head depth: 9.375" (37.5" ÷ 4)
- Temperature compensation (if sensor provided)

### Example 2: 250 Gallon LP Tank

```yaml
Name: Small Propane Tank
Source sensor: sensor.small_tank_level
Temperature sensor: sensor.small_tank_temperature  # Optional
Tank capacity: 250 gallon
Tank diameter: 30  # Auto-filled
End cap type: Ellipsoidal (typical)
```

### Example 3: Custom Tank with Flat Ends (No Temperature Compensation)

```yaml
Name: Custom Cylindrical Tank
Source sensor: sensor.custom_tank_level
Tank capacity: Custom
Tank diameter: 48
End cap type: Flat
```

## Source Sensor Requirements

The source sensor must provide the fill height in inches. Common source types:

- **Ultrasonic distance sensors**: Mount at top, measures distance to liquid surface
  - Convert to fill height: `fill_height = tank_diameter - measured_distance`
- **Pressure sensors**: Convert pressure to height
  - `fill_height = pressure / (liquid_density × gravity)`
- **Capacitive level sensors**: Usually provide fill height directly

## Attributes

The sensor exposes the following attributes:

- `source_entity`: The entity ID of the source sensor
- `tank_diameter_inches`: Tank diameter in inches
- `fill_height_inches`: Current fill height in inches
- `end_cap_type`: Type of end caps (flat or ellipsoidal_2_1)
- `cylinder_length_inches`: Length of cylindrical section (if applicable)
- `temperature_entity`: The entity ID of the temperature sensor (if configured)
- `temperature`: Current liquid temperature (if temperature sensor configured)
- `temperature_unit`: Unit of temperature measurement (°F or °C, if temperature sensor configured)

## Troubleshooting

### Incorrect Volume Readings

1. **Verify tank capacity selection**: Ensure you selected the correct gallon size for your tank
2. **Check diameter**: If using custom, verify the diameter matches your tank
3. **Check source sensor**: Ensure it provides accurate fill height in inches
4. **Confirm end cap type**: Most LP tanks have ellipsoidal heads, not flat

### Sensor Shows "Unknown" or "Unavailable"

1. **Source sensor unavailable**: Check that your source sensor is working
2. **Invalid configuration**: Verify all required fields are filled in correctly
3. **Non-numeric source**: Ensure source sensor provides numeric values

### Volume Percentage Seems Wrong

1. **Compare with known levels**: Fill tank to 25%, 50%, 75% and verify readings
2. **For ellipsoidal heads**: Remember that fill percentage is NOT linear with height
   - At 50% height, volume will be less than 50% due to head shape
   - This is normal and expected behavior
3. **Check capacity preset**: Verify you selected the correct tank size (250, 330, 500, 1000 gal)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Development

This repository includes a devcontainer configuration for easy development with Visual Studio Code.

### Using the Devcontainer

1. Install [Docker](https://www.docker.com/products/docker-desktop) and [Visual Studio Code](https://code.visualstudio.com/)
2. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) in VS Code
3. Clone this repository and open it in VS Code
4. When prompted, click "Reopen in Container" (or use Command Palette: "Dev Containers: Reopen in Container")
5. The container will build automatically and install all dependencies

### Available VS Code Tasks

Once inside the devcontainer, you can run various tasks from the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`):

- **Run Tests**: Execute the test suite with pytest
- **Run Tests with Coverage**: Run tests and display code coverage report
- **Lint with Flake8**: Check code style and quality
- **Setup: Install Test Dependencies**: Install testing requirements
- **Setup: Install Home Assistant**: Install Home Assistant core

To run a task:
1. Open Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "Tasks: Run Task"
3. Select the desired task from the list

### Running Tests Manually

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=custom_components/tank_volume --cov-report=term-missing -v

# Run a specific test file
pytest tests/test_sensor.py -v
```

### Linting

```bash
# Check code style
flake8 custom_components/tank_volume/ tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/pdrakeweb/ha-tank-volume/issues) page
2. Create a new issue with details about your setup and the problem
3. Include relevant logs from Home Assistant

## Credits

Developed for the Home Assistant community to provide accurate tank volume calculations for residential propane tanks and other horizontal cylindrical vessels.
