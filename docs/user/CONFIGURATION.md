# Configuration Reference

This document describes all configuration options and settings available in the Tank Volume Calculator integration.

## Integration Configuration

### Initial Setup Options

These options are configured during initial setup via the Home Assistant UI.

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| **Name** | string | Yes | "Tank Volume" | Friendly name for this tank |
| **Source sensor** | entity | Yes | - | Sensor that provides fill height in inches |
| **Temperature sensor** | entity | No | - | Optional temperature sensor in F or C |
| **Tank capacity** | select | Yes | 500 gallon | Preset tank size or Custom |
| **Tank diameter** | number | Yes | preset-dependent | Diameter in inches (required for Custom) |
| **End cap type** | select | No | Ellipsoidal | Ellipsoidal (typical) or Flat |

### Options Flow (Reconfiguration)

After initial setup, you can modify settings:

1. Go to **Settings** → **Devices & Services**
2. Find "Tank Volume Calculator"
3. Click **Configure**
4. Modify settings
5. Click **Submit**

**Available options:**

- Tank capacity
- Tank diameter
- End cap type
- Temperature sensor (optional)

## Entity Configuration

### Entity Customization

Customize entities via the UI or `configuration.yaml`:

#### Via Home Assistant UI

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Find and click the entity
3. Click the settings icon
4. Modify:
   - Entity ID
   - Name
   - Icon
   - Area assignment

#### Via configuration.yaml

```yaml
homeassistant:
  customize:
    sensor.my_tank_volume:
      friendly_name: "Propane Tank"
      icon: mdi:gas-cylinder
```

### Disabling Entities

If you don't need certain entities:

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Find the entity
3. Click it, then click **Settings** icon
4. Toggle **Enable entity** off

Disabled entities won't update or consume resources.

## Services

This integration does not currently register any services.

## Troubleshooting Configuration

### Config Entry Fails to Load

If the integration fails to load after configuration:

1. Check Home Assistant logs for errors
2. Verify the source sensor exists and is numeric
3. Try removing and re-adding the integration

### Options Don't Save

If configuration changes aren't persisted:

1. Check for validation errors in the UI
2. Ensure values are within allowed ranges
3. Review logs for detailed error messages
4. Try restarting Home Assistant

## Related Documentation

- [Getting Started](./GETTING_STARTED.md) - Installation and initial setup
- [GitHub Issues](https://github.com/pdrakeweb/ha-tank-volume/issues) - Report problems
