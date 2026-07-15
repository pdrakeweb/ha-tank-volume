# Tank Volume Calculator for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

A Home Assistant custom integration that calculates the volumetric fill percentage of horizontal
cylindrical tanks with semi-ellipsoidal (dished) end caps. It is designed for residential propane
(LP) tanks but works for any horizontal cylindrical vessel.

## Features

- **Standard LP Tank Presets**: Pre-configured settings for common 250, 330, 500, and 1000 gallon tanks
- **Accurate Volume Calculation**: Converts linear fill height measurements to volumetric fill percentage
- **Ellipsoidal Head Support**: Accounts for standard 2:1 semi-ellipsoidal end caps found on most LP tanks
- **Real-time Updates**: Automatically updates when source sensor changes
- **Easy Configuration**: Simple UI-based setup with smart defaults
- **Flexible Units**: Works with any distance sensor (ultrasonic, pressure, etc.)

**This integration will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Tank volume percentage and diagnostics attributes

## Quick Start

### Step 1: Install the Integration

**Prerequisites:** This integration requires [HACS](https://hacs.xyz/) to be installed.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pdrakeweb&repository=ha-tank-volume&category=integration)

Then:

1. Click "Download" to install the integration
2. Restart Home Assistant

<details>
<summary>Manual Installation (Advanced)</summary>

1. Download the `custom_components/tank_volume/` folder from this repository
2. Copy it to your Home Assistant `custom_components/` directory
3. Restart Home Assistant

</details>

### Step 2: Add and Configure the Integration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=tank_volume)

Or configure manually:

1. Go to **Settings** -> **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Tank Volume Calculator"

### Step 3: Adjust Settings (Optional)

After setup, you can adjust tank parameters:

1. Go to **Settings** -> **Devices & Services**
2. Find **Tank Volume Calculator**
3. Click **Configure**

## Configuration Details

### Setup

1. Go to **Settings** -> **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Tank Volume Calculator"
4. Fill in the configuration form:
   - **Name**: A friendly name for your tank
   - **Source sensor**: The entity that provides fill height in inches
   - **Tank capacity**: Select your tank size:
     - **250 gallon** (30" diameter, 92" total length)
    - **325 gallon** (30" diameter, 120" total length)
     - **500 gallon** (37.5" diameter, 120" total length)
     - **1000 gallon** (41" diameter, 194" total length)
     - **Custom** (specify your own diameter)
  - **End cap type**: Choose the geometry of your tank ends:
     - **Ellipsoidal (typical)**: Standard 2:1 semi-ellipsoidal heads (default - most LP tanks)
     - **Flat**: Pure cylinder with no end caps
5. Provide tank details:
  - **Tank diameter** (inches)
  - **Tank total length** (inches)
  - **Tank volume** (gallons)
  - Presets prefill default values; Custom starts blank

### Options

You can modify the tank parameters after setup:

1. Go to **Settings** -> **Devices & Services**
2. Find the Tank Volume Calculator integration
3. Click **Configure**
4. Update the values as needed

## Temperature Compensation

Propane expands and contracts with temperature, so the measured liquid level (and
therefore the calculated volume) drifts with the weather even when no gas is being
consumed. If you provide an optional **temperature sensor**, the integration adds two
extra `... (temperature adjusted)` sensors that normalise the reading to a reference
temperature of 60 °F (15.6 °C).

Four settings control the correction:

| Setting | Default | Purpose |
|---------|---------|---------|
| **Temperature adjustment coefficient** | `0.0022` /°F | Effective volumetric expansion coefficient. `ΔV/V ≈ coefficient × ΔT`. Because the correction scales a percentage of volume, it automatically tracks how full the tank is. |
| **Temperature lag at 60 °F (hours)** | `5` | The transport delay applied to the temperature at the 60 °F reference. |
| **Temperature lag slope (hours per °F)** | `0.067` | How much that delay grows per °F of *seasonal* temperature above 60 °F. |
| **Temperature smoothing (hours)** | `1` | Averaging window applied around the delayed reading to suppress sensor noise. |

### Why the lag matters, and why it is temperature dependent

The propane's *bulk* temperature — the thing that actually drives expansion — is a
**delayed, low-passed** version of what the sensor reports. A Mopeka-style sensor is
clamped to the *outside* of the tank bottom, so it tracks the tank skin / ambient, which
changes faster than the bulk liquid. The reported temperature therefore *leads* the
volume response, and compensating against the *instantaneous* reading corrects at the
wrong phase — it can make the daily swing *worse*.

A full year of tank data (4–84 °F, a wide range of fill levels) shows the lead is
**strongly temperature dependent** and — once temperature is held fixed — **independent
of how full the tank is**:

```
lag_hours ≈ 5.0 + 0.067 × (T_seasonal − 60 °F)     # ~2–3 h cold, ~6–7 h warm
```

The integration reconstructs the bulk temperature by looking back this
temperature-dependent delay (the delay is chosen from a slow, ~24 h seasonal temperature
average so it doesn't wobble with the daily cycle) plus a small smoothing window, then
applies the expansion correction. In field data this flattens the repeatable daily volume
swing from ~7 gal to ~1–2 gal on a 500 gal tank across the whole year — and, unlike a
fixed lag, it does **not** degrade in winter (a fixed 5 h lag applied in cold weather is
worse than no correction at all).

Set **Temperature lag slope** to `0` for a constant lag, and both the lag and slope to `0`
to disable the delay entirely and use the instantaneous reading (the pre-1.1 behaviour).

**Tuning:** the coefficient and lag depend on your sensor. To calibrate, chart a
`... (temperature adjusted)` sensor over a few clear days during a period of little or no
usage and adjust the settings until the daily curve is as flat as possible. The adjusted
sensors expose `temperature_lag_hours`, `temperature_lag_per_degree`,
`temperature_smoothing_hours`, the current `effective_lag_hours`, and the
`bulk_temperature_f` estimate as attributes to help.

## Burn Rate & Monthly Cost

When a **tank volume** is configured, the integration also adds burn-rate sensors that
estimate consumption and monthly cost from the (temperature-adjusted) contents volume:

| Sensor | Unit | Description |
|--------|------|-------------|
| `... Burn rate` | gal/day | Average daily consumption |
| `... Monthly burn` | gal | Burn rate × days in the current month |
| `... Monthly cost` | your HA currency | Monthly burn × price per gallon (unavailable until a price is set) |

The burn rate is a **least-squares trend of the contents volume over a multi-day window**,
not an endpoint difference. This matters: over a short window (e.g. 72 h) the real
consumption can be smaller than the sensor's noise, so an endpoint-based rate swings wildly
positive and negative and, extrapolated to a month, explodes. Averaging ~7 days rejects the
noise (and the roughly zero-mean daily thermal wave) and gives a stable estimate. **Refills
are detected as a large upward jump and the trend is measured only over the data since the
most recent refill**, so a fill-up never reads as negative consumption.

**Startup / warm-up.** The multi-day trend normally needs about half a window of readings
before it's trustworthy. To avoid sitting at `Unknown` after install or a restart, the burn
sensors fill in as soon as possible: on startup they backfill from the recorder's history of
the contents-volume entity, and a brand-new sensor with no history falls back to a rough
estimate from its first couple of readings that self-corrects as the window fills. While a
value is this provisional estimate, the sensor carries a `provisional: true` attribute; it
clears to `false` once the full-window fit takes over. Treat provisional values as rough.

Settings (in the integration's **Configure** / options):

| Setting | Default | Purpose |
|---------|---------|---------|
| **Burn-rate averaging window** | `3 days` | `24 hours`, `3 days`, or `7 days`. Shorter reacts faster to a weather change but is noisier; longer is steadier but slower. |
| **Weight recent readings more** | off | Recency-weights the trend within the window (weights halve every window/6 back), so it reacts faster while still smoothing. A weighted 7-day window lands between the stability of 7 days and the responsiveness of 3. |
| **Propane price per gallon** | `0` | Fixed price for the cost sensor. `0` leaves the cost sensor unavailable unless a price entity is set. |
| **Price per gallon entity** | — | Optional `input_number`/`sensor` giving the current price. If set, it overrides the fixed price. |

Roughly, on this tank's data (monthly-cost stability / days to react to a 2→6 gal/day step):
`24 h` ≈ ±$350 / 0.8 d · `3 days` ≈ ±$190 / 2.3 d · `7 days` ≈ ±$145 / 5.3 d · `7 days weighted` ≈ ±$166 / 4.2 d.

At low consumption (e.g. summer) the tank is nearly flat and the true burn can be below the
sensor's noise floor, so the estimate is inherently uncertain then — but the dollar amounts
are correspondingly small. The estimate is most useful and most stable during the heating
season, where a 7-day window settles to within a few percent.

## Standard LP Tank Specifications

Based on common residential propane tank dimensions:

| Capacity | Diameter | Total Length | Cylinder Length* | Head Depth* |
|----------|----------|--------------|------------------|-------------|
| 250 gal  | 30"      | 92"          | 77"              | 7.5"        |
| 330 gal  | 30"      | 120"         | 105"             | 7.5"        |
| 500 gal  | 37.5"    | 120"         | 101.25"          | 9.375"      |
| 1000 gal | 41"      | 190"         | 169.5"           | 10.25"      |

*Calculated automatically for ellipsoidal heads (head depth = diameter / 4)

## Tank Geometry Types

### Ellipsoidal (Typical) - Default

The most common type for residential and commercial LP tanks. These heads have a standard 2:1
elliptical ratio where the depth of each head is exactly 1/4 of the tank diameter.

**Configuration:**
- End cap type: `Ellipsoidal (typical)`
- Cylinder length: Automatically calculated from tank capacity and diameter

**How it works:**
- For a 500 gallon tank (37.5" diameter, 120" total length):
  - Each head depth: 9.375" (37.5 / 4)
  - Cylinder length: 101.25" (120 - 2 * 9.375)
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
- You are using a custom cylindrical tank

## Mathematical Background

### Pure Cylinder (Flat Ends)

For a horizontal cylinder with radius `r` and liquid fill height `h`:

The cross-sectional area of liquid is a circular segment:
```
A(h) = r^2 * arccos((r - h) / r) - (r - h) * sqrt(2 * r * h - h^2)
```

Volumetric fill percentage:
```
Fill % = [A(h) / (pi * r^2)] * 100
```

### Ellipsoidal Heads (2:1 Ratio)

For a semi-ellipsoidal head with radius `r`, head depth `a = r/2`, and fill height `h`:

Volume of liquid in one head (let `y = h - r`):
```
V_head(h) = 0.5 * pi * r * a * (y - (y^3 / (3 * r^2)) + (2/3) * r)
```

Total tank volume at height `h`:
```
V_total(h) = [Cylinder cross-section * L] + [2 * V_head(h)]
```

Where `L` is the cylinder length (total length minus 2 * head depth).

Total capacity:
```
V_capacity = pi * r^2 * L + 2 * [(2/3) * pi * r^2 * a]
```

Fill percentage:
```
Fill % = [V_total(h) / V_capacity] * 100
```

## Example Configurations

### Example 1: Standard 500 Gallon LP Tank

```yaml
Name: Propane Tank
Source sensor: sensor.propane_ultrasonic_distance
Tank capacity: 500 gallon
Tank diameter: 37.5  # Auto-filled
End cap type: Ellipsoidal (typical)  # Default
```

The integration automatically calculates:
- Cylinder length: 101.25" (120" total - 2 * 9.375" heads)
- Head depth: 9.375" (37.5" / 4)

### Example 2: 250 Gallon LP Tank

```yaml
Name: Small Propane Tank
Source sensor: sensor.small_tank_level
Tank capacity: 250 gallon
Tank diameter: 30  # Auto-filled
End cap type: Ellipsoidal (typical)
```

### Example 3: Custom Tank with Flat Ends

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
  - `fill_height = pressure / (liquid_density * gravity)`
- **Capacitive level sensors**: Usually provide fill height directly

## Attributes

The sensor exposes the following attributes:

- `source_entity`: The entity ID of the source sensor
- `tank_diameter_inches`: Tank diameter in inches
- `fill_height_inches`: Current fill height in inches
- `end_cap_type`: Type of end caps (flat or ellipsoidal_2_1)
- `cylinder_length_inches`: Length of cylindrical section (if applicable)

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
  - At 50% height, volume should be 50% for symmetric heads
3. **Check capacity preset**: Verify you selected the correct tank size (250, 330, 500, 1000 gal)

### Enable Debug Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.tank_volume: debug
```

## Contributing

Contributions are welcome. Please feel free to submit a Pull Request.

## Development

This repository includes a devcontainer configuration for easy development with Visual Studio Code.

### Cloud Development (Optional)

Use GitHub Codespaces to start a cloud dev environment:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/pdrakeweb/ha-tank-volume?quickstart=1)

### Local Development

1. Install [Docker](https://www.docker.com/products/docker-desktop) and [Visual Studio Code](https://code.visualstudio.com/)
2. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) in VS Code
3. Clone this repository and open it in VS Code
4. When prompted, click "Reopen in Container" (or use Command Palette: "Dev Containers: Reopen in Container")
5. The container will build automatically and install all dependencies
6. Start Home Assistant inside the devcontainer by running `./script/develop` or the VS Code task

### Available VS Code Tasks

From the Command Palette (Tasks: Run Task):

- **Run Home Assistant (Development Mode)**: Start Home Assistant for local testing
- **Run Tests**: Execute the test suite
- **Run Tests with Coverage**: Run tests with coverage output
- **Lint (Ruff Format + Check)**: Format and lint
- **Lint Check (Read-Only)**: Lint without formatting
- **Type Check**: Run static type checking
- **Check All (Type + Lint)**: Full validation
- **Hassfest**: Validate integration structure
- **Spell Check**: Run spell check
- **Setup (Bootstrap/Setup/Reset)**: Prepare or reset the dev environment

### Running Commands Manually

```bash
# Start Home Assistant
./script/develop

# Run tests
./script/test -v

# Run tests with coverage
./script/test --cov-html

# Lint and type check
./script/check
```

### Releasing (HACS)

Releases are published as GitHub Releases with the integration attached as a clean
`tank_volume.zip` (`hacs.json` sets `zip_release`), which is what HACS downloads for
everyone who has the integration installed.

From a green `main` (the Validate workflow runs on every push):

```bash
./script/release            # tag & release the version currently in manifest.json
./script/release 1.4.1      # bump manifest to 1.4.1, commit "Release v1.4.1", then release
./script/release --dry-run  # build the zip and run checks only (no tag/push)
```

The script verifies a clean state and that the tag doesn't already exist, builds a local
`dist/tank_volume.zip` so you can inspect exactly what ships, then creates and pushes the
`vX.Y.Z` tag. Pushing the tag triggers `.github/workflows/release.yml`, which rebuilds the
zip in CI, verifies it matches `manifest.json`, and publishes the GitHub Release. HACS then
offers the new version to installed users. **The tag must equal the manifest `version`.**

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/pdrakeweb/ha-tank-volume/issues) page
2. Create a new issue with details about your setup and the problem
3. Include relevant logs from Home Assistant

## Credits

Developed for the Home Assistant community to provide accurate tank volume calculations for residential propane tanks and other horizontal cylindrical vessels.

[commits-shield]: https://img.shields.io/github/commit-activity/y/pdrakeweb/ha-tank-volume.svg?style=for-the-badge
[commits]: https://github.com/pdrakeweb/ha-tank-volume/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/pdrakeweb/ha-tank-volume.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40pdrakeweb-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/pdrakeweb/ha-tank-volume.svg?style=for-the-badge
[releases]: https://github.com/pdrakeweb/ha-tank-volume/releases
