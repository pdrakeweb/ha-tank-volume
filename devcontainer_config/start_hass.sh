#!/bin/bash
# Script to start Home Assistant in the devcontainer for testing

set -e

# Set up directory structure
CONFIG_DIR="${HOME}/.homeassistant"
REPO_DIR="/workspaces/ha-tank-volume"

# Use current directory if not in workspace (for CI/testing)
if [ ! -d "$REPO_DIR" ]; then
    REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

echo "Setting up Home Assistant configuration..."

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Copy configuration
echo "Copying example configuration..."
cp "$REPO_DIR/devcontainer_config/configuration.yaml" "$CONFIG_DIR/"

# Create custom_components directory and symlink our integrations
echo "Setting up custom components..."
mkdir -p "$CONFIG_DIR/custom_components"
ln -sf "$REPO_DIR/custom_components/tank_volume" "$CONFIG_DIR/custom_components/tank_volume"
ln -sf "$REPO_DIR/custom_components/mock_tank_height_sensor" "$CONFIG_DIR/custom_components/mock_tank_height_sensor"

echo ""
echo "Configuration complete!"
echo "Custom components installed:"
echo "  - tank_volume"
echo "  - mock_tank_height_sensor"
echo ""
echo "Starting Home Assistant..."
echo "Once started, access it at: http://localhost:8123"
echo ""
echo "To change mock sensor values, use Developer Tools > Services:"
echo "  Service: mock_tank_height_sensor.set_value"
echo "  Entity: sensor.propane_tank_height"
echo "  Value: <height in inches>"
echo ""

# Start Home Assistant
hass -c "$CONFIG_DIR"
