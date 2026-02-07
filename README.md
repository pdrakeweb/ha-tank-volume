# Tank Volume Calculator for Home Assistant

A Home Assistant custom integration that calculates the volumetric fill percentage of horizontal cylindrical tanks with optional semi-ellipsoidal (dished) end caps.

## Features

- **Accurate Volume Calculation**: Converts linear fill height measurements to volumetric fill percentage
- **Multiple Tank Geometries**: Supports flat ends (pure cylinder), standard 2:1 ellipsoidal heads, and custom ellipsoidal heads
- **Real-time Updates**: Automatically updates when source sensor changes
- **Easy Configuration**: Simple UI-based setup through Home Assistant
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
   - **Tank diameter**: The internal diameter of the tank in inches
   - **End cap type**: Choose the geometry of your tank ends:
     - **Flat (pure cylinder)**: No end caps - pure cylindrical tank (default)
     - **2:1 Ellipsoidal**: Standard semi-ellipsoidal (2:1 ratio) dished heads
     - **Custom Ellipsoidal**: Custom ellipsoidal heads with specific depth
   - **Cylinder length**: Length of the cylindrical body section in inches (excluding end caps) - required for ellipsoidal heads
   - **End cap depth**: Depth of each ellipsoidal head in inches - only for custom ellipsoidal type

### Options

You can modify the tank parameters after setup:

1. Go to **Settings** → **Devices & Services**
2. Find the Tank Volume Calculator integration
3. Click **Configure**
4. Update the values as needed

## Tank Geometry Types

### Flat (Pure Cylinder)

A simple horizontal cylinder with flat ends. This is the default and maintains backward compatibility.

**Configuration:**
- End cap type: `Flat (pure cylinder)`
- Only tank diameter is needed

**Use when:**
- Your tank has flat ends
- You want to measure a section of pipe
- You're migrating from an earlier version

### 2:1 Ellipsoidal Heads

The most common type for commercial and industrial tanks. These heads have a standard 2:1 elliptical ratio where the depth of each head is exactly 1/4 of the tank diameter.

**Configuration:**
- End cap type: `2:1 Ellipsoidal`
- Cylinder length: Length of the straight cylindrical section (excluding the heads)
- End cap depth: Automatically calculated as diameter ÷ 4

**Example:**
For a 48-inch diameter tank with 96-inch cylinder length:
- Diameter: 48 inches
- Cylinder length: 96 inches
- Each head depth: 12 inches (automatically calculated)
- Total tank length: 96 + 12 + 12 = 120 inches

### Custom Ellipsoidal Heads

For tanks with non-standard ellipsoidal heads where you know the specific depth of each head.

**Configuration:**
- End cap type: `Custom Ellipsoidal`
- Cylinder length: Length of the straight cylindrical section
- End cap depth: The actual depth of each head in inches

**Use when:**
- Your tank has non-standard ellipsoidal heads
- You know the exact head depth from tank specifications

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

### Semi-Ellipsoidal Heads

For a semi-ellipsoidal head with radius `r`, head depth `a`, and fill height `h`:

Volume of liquid in one head:
```
V_head(h) = (π × a / (3 × r²)) × h² × (3r - h)
```

For 2:1 heads where `a = r/2`:
```
V_head(h) = (π × h² × (3r - h)) / (6 × r)
```

Total tank volume at height `h`:
```
V_total(h) = [Cylinder cross-section × L] + [2 × V_head(h)]
```

Where `L` is the cylinder length.

Total capacity:
```
V_capacity = π × r² × L + 2 × [(2/3) × π × r² × a]
```

Fill percentage:
```
Fill % = [V_total(h) / V_capacity] × 100
```

## Example Configurations

### Example 1: Simple Propane Tank (Flat Ends)

```yaml
Name: Propane Tank
Source sensor: sensor.propane_ultrasonic_distance
Tank diameter: 24
End cap type: Flat (pure cylinder)
```

### Example 2: Industrial Tank (2:1 Ellipsoidal)

```yaml
Name: Water Storage Tank
Source sensor: sensor.water_level
Tank diameter: 60
End cap type: 2:1 Ellipsoidal
Cylinder length: 144
# Head depth automatically = 15 inches (60/4)
# Total length = 144 + 15 + 15 = 174 inches
```

### Example 3: Custom Tank (Custom Ellipsoidal)

```yaml
Name: Custom Fuel Tank
Source sensor: sensor.fuel_level
Tank diameter: 48
End cap type: Custom Ellipsoidal
Cylinder length: 96
End cap depth: 10
# Total length = 96 + 10 + 10 = 116 inches
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
- `end_cap_type`: Type of end caps (flat, ellipsoidal_2_1, or ellipsoidal_custom)
- `cylinder_length_inches`: Length of cylindrical section (if applicable)
- `end_cap_depth_inches`: Depth of end caps (if applicable)

## Troubleshooting

### Incorrect Volume Readings

1. **Verify tank dimensions**: Double-check diameter, length, and head depth
2. **Check source sensor**: Ensure it provides accurate fill height in inches
3. **Confirm end cap type**: Make sure you selected the correct geometry for your tank

### Sensor Shows "Unknown" or "Unavailable"

1. **Source sensor unavailable**: Check that your source sensor is working
2. **Invalid configuration**: Verify all required fields are filled in correctly
3. **Non-numeric source**: Ensure source sensor provides numeric values

### Volume Percentage Seems Wrong

1. **Compare with known levels**: Fill tank to 25%, 50%, 75% and verify readings
2. **For ellipsoidal heads**: Remember that fill percentage is NOT linear with height
   - At 50% height, volume will be less than 50% due to head shape
3. **Verify cylinder length**: For tanks with heads, ensure cylinder length excludes head depths

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/pdrakeweb/ha-tank-volume/issues) page
2. Create a new issue with details about your setup and the problem
3. Include relevant logs from Home Assistant

## Credits

Developed for the Home Assistant community to provide accurate tank volume calculations for various industrial and residential applications.
