<a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge"></a>
<a href="https://www.gnu.org/licenses/gpl-3.0"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg?style=for-the-badge"></a>
<a href="https://github.com/pdrakeweb/ha-tank-volume/releases"><img src="https://img.shields.io/github/v/release/pdrakeweb/ha-tank-volume?style=for-the-badge"></a>
<a href="https://www.home-assistant.io/"><img src="https://img.shields.io/badge/Home%20Assistant-2026.1+-blue.svg?style=for-the-badge&logo=homeassistant"></a>

# 🛢️ Tank Volume Calculator for Home Assistant

A HACS-compatible custom integration that converts a horizontal cylindrical tank's fill height (in inches) to a mathematically correct volumetric percentage. This integration provides accurate volume calculations based on circular segment geometry—**not** simple linear approximations. A tank filled to 50% of its height does NOT hold 50% of its volume due to the circular cross-section geometry.

## Table of Contents

- [✨ Features](#-features)
- [📐 How It Works](#-how-it-works)
- [📦 Installation](#-installation)
  - [Via HACS (Recommended)](#via-hacs-recommended)
  - [Manual Installation](#manual-installation)
- [⚙️ Configuration](#️-configuration)
- [📊 Sensor Attributes](#-sensor-attributes)
- [🎨 Dashboard Examples](#-dashboard-examples)
- [🤖 Automation Examples](#-automation-examples)
- [📝 Template Alternative](#-template-alternative)
- [🔧 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

## ✨ Features

- **Mathematically accurate volumetric percentage** using circular segment formula
- **UI-based configuration** (no YAML needed)
- **Real-time updates** when source sensor changes
- **Works with any sensor** reporting fill height in inches
- **Supports multiple tanks** (add the integration multiple times)
- **Extra state attributes** (source_entity, tank_diameter_inches, fill_height_inches)
- **Proper device grouping** in Home Assistant
- **Configurable display precision**
- **Options flow** to change diameter after setup

## 📐 How It Works

This integration uses the mathematical formula for calculating the area of a circular segment to determine the volumetric fill percentage of a horizontal cylindrical tank.

### The Formula

Given a circular cross-section with radius `r` and fill height `h`, the area of the liquid segment is:

```
A(h) = r² · arccos((r − h) / r) − (r − h) · √(2rh − h²)
Volume % = A(h) / (π · r²) × 100
```

### Non-Linear Relationship

The relationship between fill height and volume is **non-linear** due to the circular geometry:

| Fill Height (% of diameter) | Volume % |
|------------------------------|----------|
| 10%                          | 5.2%     |
| 25%                          | 19.5%    |
| 50%                          | 50.0%    |
| 75%                          | 80.5%    |
| 90%                          | 94.8%    |

**Important:** This calculation is **independent of tank length**. The volumetric percentage is the same regardless of how long the cylinder is, because we're calculating the cross-sectional area ratio.

## 📦 Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click the three-dot menu in the top right corner
3. Select **Custom repositories**
4. Add this repository URL: `https://github.com/pdrakeweb/ha-tank-volume`
5. Select **Integration** as the category
6. Click **Add**
7. Click **Download** on the Tank Volume Calculator card
8. Restart Home Assistant

[![Open HACS Repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pdrakeweb&repository=ha-tank-volume&category=integration)

### Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/tank_volume` directory to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## ⚙️ Configuration

This integration uses the UI-based config flow—**no YAML editing required**.

### Setup Steps

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Tank Volume Calculator**
4. Fill in the configuration form

### Configuration Fields

| Field           | Description                                                    | Required | Default        |
|-----------------|----------------------------------------------------------------|----------|----------------|
| Sensor Name     | Friendly name for the volume sensor                            | Yes      | "Tank Volume"  |
| Source Sensor   | Existing sensor entity reporting fill height in inches         | Yes      | —              |
| Tank Diameter   | Internal diameter of the horizontal cylinder in inches         | Yes      | —              |

### Updating Configuration

After initial setup, you can update the tank diameter by clicking **Configure** on the integration card in Devices & Services.

## 📊 Sensor Attributes

The sensor exposes the following extra state attributes:

| Attribute              | Description                              |
|------------------------|------------------------------------------|
| `source_entity`        | Entity ID of the source height sensor    |
| `tank_diameter_inches` | Configured tank diameter in inches       |
| `fill_height_inches`   | Current fill height reading from sensor  |

## 🎨 Dashboard Examples

### Gauge Card with Severity Colors

```yaml
type: gauge
entity: sensor.tank_volume
min: 0
max: 100
severity:
  green: 40
  yellow: 20
  red: 0
needle: true
name: Propane Tank
```

### Entities Card

```yaml
type: entities
title: Tank Information
entities:
  - entity: sensor.tank_volume
    name: Volume Percentage
  - type: attribute
    entity: sensor.tank_volume
    attribute: fill_height_inches
    name: Fill Height
    suffix: '"'
  - type: attribute
    entity: sensor.tank_volume
    attribute: tank_diameter_inches
    name: Tank Diameter
    suffix: '"'
```

### Mushroom Gauge Card

```yaml
type: custom:mushroom-gauge-card
entity: sensor.tank_volume
name: Tank Level
fill: green
```

## 🤖 Automation Examples

### Low Tank Alert

```yaml
automation:
  - alias: "Low Tank Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.tank_volume
        below: 20
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Low Tank Level"
          message: "Tank is at {{ states('sensor.tank_volume') }}%. Time to refill!"
```

### Tank Refill Notification

```yaml
automation:
  - alias: "Tank Refilled"
    trigger:
      - platform: numeric_state
        entity_id: sensor.tank_volume
        above: 80
    condition:
      - condition: template
        value_template: >
          {{ (as_timestamp(now()) - as_timestamp(state_attr('automation.tank_refilled', 'last_triggered') | default(0))) > 86400 }}
    action:
      - service: notify.mobile_app
        data:
          title: "✅ Tank Refilled"
          message: "Tank is now at {{ states('sensor.tank_volume') }}%"
```

## 📝 Template Alternative

For advanced users who prefer not to install a custom integration, you can use this Jinja2 template sensor instead. However, **the integration is recommended** as it provides better device grouping, options flow, and state management.

```yaml
template:
  - sensor:
      - name: "Tank Volume"
        unique_id: tank_volume_template
        unit_of_measurement: "%"
        state_class: measurement
        icon: mdi:storage-tank
        state: >
          {% set h = states('sensor.tank_fill_height') | float(0) %}
          {% set d = 24.0 %}  {# Replace with your tank diameter #}
          {% set r = d / 2.0 %}
          {% if h <= 0 %}0
          {% elif h >= d %}100
          {% else %}
            {% set term1 = r * r * (((r - h) / r) | acos) %}
            {% set term2 = (r - h) * ((2 * r * h - h * h) | sqrt) %}
            {% set segment = term1 - term2 %}
            {% set circle = 3.14159265359 * r * r %}
            {{ ((segment / circle) * 100) | round(1) }}
          {% endif %}
```

## 🔧 Troubleshooting

| Problem                               | Solution                                                                                     |
|---------------------------------------|----------------------------------------------------------------------------------------------|
| Sensor shows as "Unavailable"         | Check that the source sensor exists and is reporting numeric values in inches                |
| Volume percentage seems incorrect     | Verify the tank diameter is correct. Remember: 50% height ≠ 50% volume!                     |
| Integration not found after install   | Restart Home Assistant after installation. Clear browser cache if needed.                    |
| Can't add integration twice           | Each integration instance needs a unique sensor name to avoid conflicts                      |
| Source sensor state is "unknown"      | The source sensor must be available and reporting a valid numeric value                      |
| Wrong values after changing diameter  | Go to the integration in Devices & Services and click Configure to update the diameter      |

### Debug Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.tank_volume: debug
```

## 🤝 Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue on GitHub. Pull requests are also appreciated.

## 📄 License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for the Home Assistant community**
