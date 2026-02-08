# Getting Started with Tank Volume Calculator

This guide will help you install and set up the Tank Volume Calculator custom integration for Home Assistant.

## Prerequisites

- Home Assistant 2025.12.3 or newer
- HACS (Home Assistant Community Store) installed
- A source sensor that provides fill height in inches

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/pdrakeweb/ha-tank-volume`
6. Set category to "Integration"
7. Click "Add"
8. Find "Tank Volume Calculator" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/pdrakeweb/ha-tank-volume/releases)
2. Extract the `tank_volume` folder from the archive
3. Copy it to `custom_components/tank_volume/` in your Home Assistant configuration directory
4. Restart Home Assistant

## Initial Setup

After installation, add the integration:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Tank Volume Calculator"
4. Fill in the configuration form:
   - **Name**: Friendly name for the tank
   - **Source sensor**: Entity that reports fill height in inches
   - **Tank capacity**: Select a preset or Custom
   - **Tank diameter**: Diameter in inches (required for Custom)
   - **End cap type**: Ellipsoidal (typical) or Flat
   - **Temperature sensor** (optional): For temperature compensation
5. Click **Submit** to complete setup

## Troubleshooting

### Entities Not Updating

If entities show "Unavailable" or don't update:

1. Check that the source sensor is updating
2. Verify the fill height is numeric
3. Review logs: **Settings** → **System** → **Logs**
4. Try reloading the integration

### Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: warning
  logs:
    custom_components.tank_volume: debug
```

Add this to `configuration.yaml`, restart, and reproduce the issue. Check logs for detailed information.

## Next Steps

- See [CONFIGURATION.md](./CONFIGURATION.md) for detailed configuration options
- Report issues at [GitHub Issues](https://github.com/pdrakeweb/ha-tank-volume/issues)

## Support

For help and discussion:

- [GitHub Discussions](https://github.com/pdrakeweb/ha-tank-volume/discussions)
- [Home Assistant Community Forum](https://community.home-assistant.io/)
