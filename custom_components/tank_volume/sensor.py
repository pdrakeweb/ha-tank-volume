"""Tank Volume Calculator sensor platform."""

from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, PERCENTAGE
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_CYLINDER_LENGTH,
    CONF_END_CAP_TYPE,
    CONF_SOURCE_ENTITY,
    CONF_TANK_DIAMETER,
    DOMAIN,
    END_CAP_ELLIPSOIDAL_2_1,
    END_CAP_FLAT,
)

_LOGGER = logging.getLogger(__name__)


def compute_horizontal_cylinder_volume_percentage(fill_height_inches: float, diameter_inches: float) -> float | None:
    """
    Calculate the volumetric fill percentage for a horizontal cylindrical tank.

    For a horizontal cylinder with radius r and liquid fill height h:
    The cross-sectional area of the liquid is a circular segment:
    A(h) = r² · arccos((r - h) / r) - (r - h) · √(2rh - h²)

    The full circle area is π · r²
    Volumetric fill percentage = A(h) / (π · r²) × 100

    Args:
        fill_height_inches: The liquid fill height in inches (0 ≤ h ≤ diameter)
        diameter_inches: The tank internal diameter in inches

    Returns:
        The volumetric fill percentage (0-100), or None if diameter is invalid
    """
    # Validate diameter
    if diameter_inches <= 0:
        return None

    # Clamp fill height to valid range
    h = max(0, min(fill_height_inches, diameter_inches))
    r = diameter_inches / 2.0

    # Handle edge cases
    if h <= 0:
        return 0.0
    if h >= diameter_inches:
        return 100.0

    # Calculate the circular segment area
    # A(h) = r² · arccos((r - h) / r) - (r - h) · √(2rh - h²)
    try:
        # First term: r² · arccos((r - h) / r)
        arccos_term = r * r * math.acos((r - h) / r)

        # Second term: (r - h) · √(2rh - h²)
        sqrt_term = (r - h) * math.sqrt(2 * r * h - h * h)

        # Circular segment area
        segment_area = arccos_term - sqrt_term

        # Full circle area
        circle_area = math.pi * r * r
    except (ValueError, ZeroDivisionError):
        return None
    else:
        return (segment_area / circle_area) * 100.0


def compute_ellipsoidal_head_volume(
    fill_height: float,
    radius: float,
    head_depth: float,
) -> float:
    """
    Calculate liquid volume in one semi-ellipsoidal head at given fill height.

    Args:
        fill_height: Liquid height in the tank (0 to diameter)
        radius: Tank radius (diameter / 2)
        head_depth: Depth of the ellipsoidal head

    Returns:
        Volume in cubic inches (or same unit³ as inputs)
    """
    if fill_height <= 0:
        return 0.0

    diameter = 2 * radius
    if fill_height >= diameter:
        # Full head - return total volume
        return (2.0 / 3.0) * math.pi * radius * radius * head_depth

    h = max(0.0, min(fill_height, diameter))
    r = radius
    a = head_depth

    # Integrate half-ellipsoid cross-section areas from y = -r to y = -r + h.
    # Volume = 0.5 * pi * r * a * (y - y^3 / (3 r^2)) |_{-r}^{h - r}
    y = h - r
    return 0.5 * math.pi * r * a * (y - (y**3) / (3.0 * r * r) + (2.0 / 3.0) * r)


def compute_tank_volume_with_heads(
    fill_height: float,
    diameter: float,
    cylinder_length: float,
    end_cap_type: str = END_CAP_FLAT,
) -> float | None:
    """
    Calculate volumetric fill percentage for horizontal tank with optional ellipsoidal heads.

    Args:
        fill_height: Liquid fill height in inches
        diameter: Tank diameter in inches
        cylinder_length: Length of cylindrical section in inches
        end_cap_type: "flat" or "ellipsoidal_2_1"

    Returns:
        Fill percentage (0-100) or None if invalid
    """
    # Validate inputs
    if diameter <= 0 or cylinder_length <= 0:
        return None

    # Clamp fill height to valid range
    h = max(0.0, min(fill_height, diameter))
    r = diameter / 2.0

    # Handle edge cases
    if h <= 0:
        return 0.0
    if h >= diameter:
        return 100.0

    # Calculate cylinder cross-sectional area (circular segment)
    try:
        # First term: r² · arccos((r - h) / r)
        arccos_term = r * r * math.acos((r - h) / r)

        # Second term: (r - h) · √(2rh - h²)
        sqrt_term = (r - h) * math.sqrt(2 * r * h - h * h)

        # Circular segment area
        segment_area = arccos_term - sqrt_term

        # Cylinder volume
        cylinder_volume = segment_area * cylinder_length

        # Calculate head volumes based on end cap type
        if end_cap_type == END_CAP_FLAT:
            # No end caps - pure cylinder
            head_volume = 0.0
            total_head_volume = 0.0
        elif end_cap_type == END_CAP_ELLIPSOIDAL_2_1:
            # Standard 2:1 ellipsoidal heads
            head_depth = r / 2.0  # For 2:1 ratio, depth = diameter/4 = radius/2
            head_volume = 2.0 * compute_ellipsoidal_head_volume(h, r, head_depth)
            total_head_volume = 2.0 * (2.0 / 3.0) * math.pi * r * r * head_depth
        else:
            return None

        # Total volume at fill height h
        total_volume = cylinder_volume + head_volume

        # Total tank capacity
        circle_area = math.pi * r * r
        total_capacity = circle_area * cylinder_length + total_head_volume
    except (ValueError, ZeroDivisionError):
        return None
    else:
        return (total_volume / total_capacity) * 100.0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tank Volume Calculator sensor from a config entry."""
    source_entity = config_entry.data[CONF_SOURCE_ENTITY]
    tank_diameter = config_entry.options.get(CONF_TANK_DIAMETER, config_entry.data[CONF_TANK_DIAMETER])
    name = config_entry.data[CONF_NAME]

    # Get end cap configuration
    end_cap_type = config_entry.options.get(
        CONF_END_CAP_TYPE, config_entry.data.get(CONF_END_CAP_TYPE, END_CAP_ELLIPSOIDAL_2_1)
    )
    cylinder_length = config_entry.options.get(CONF_CYLINDER_LENGTH, config_entry.data.get(CONF_CYLINDER_LENGTH))

    sensor = TankVolumeSensor(
        config_entry.entry_id,
        name,
        source_entity,
        tank_diameter,
        end_cap_type,
        cylinder_length,
    )

    async_add_entities([sensor], True)


class TankVolumeSensor(SensorEntity):
    """Representation of a Tank Volume Calculator sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:storage-tank"
    _attr_suggested_display_precision = 1
    _attr_has_entity_name = True

    def __init__(
        self,
        entry_id: str,
        name: str,
        source_entity: str,
        tank_diameter: float,
        end_cap_type: str = END_CAP_ELLIPSOIDAL_2_1,
        cylinder_length: float | None = None,
    ) -> None:
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._attr_name = name
        self._source_entity = source_entity
        self._tank_diameter = tank_diameter
        self._end_cap_type = end_cap_type
        self._cylinder_length = cylinder_length
        self._fill_height: float | None = None
        self._attr_unique_id = f"{entry_id}_volume_percentage"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._attr_name,
            manufacturer="Tank Volume Calculator",
            model="Horizontal Cylinder",
            entry_type=None,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {
            "source_entity": self._source_entity,
            "tank_diameter_inches": self._tank_diameter,
            "fill_height_inches": self._fill_height,
            "end_cap_type": self._end_cap_type,
        }
        if self._cylinder_length is not None:
            attrs["cylinder_length_inches"] = self._cylinder_length
        return attrs

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()

        # Read current state of source entity
        if (state := self.hass.states.get(self._source_entity)) is not None:
            self._handle_source_state(state.state)

        # Track state changes
        self.async_on_remove(
            async_track_state_change_event(self.hass, [self._source_entity], self._async_source_changed)
        )

    @callback
    def _async_source_changed(self, event: Event) -> None:
        """Handle source entity state changes."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        self._handle_source_state(new_state.state)
        self.async_write_ha_state()

    def _handle_source_state(self, state_value: str) -> None:
        """Handle source entity state value."""
        # Handle unavailable or unknown states
        if state_value in ("unknown", "unavailable", None):
            self._attr_native_value = None
            self._fill_height = None
            return

        # Try to parse as float
        try:
            fill_height = float(state_value)
            self._fill_height = fill_height

            # Calculate volume percentage based on end cap configuration
            if self._end_cap_type == END_CAP_FLAT:
                # Pure cylinder calculation (flat ends)
                percentage = compute_horizontal_cylinder_volume_percentage(fill_height, self._tank_diameter)
            else:
                # Use cylinder length for tank with ellipsoidal heads
                cylinder_length = self._cylinder_length or self._tank_diameter
                percentage = compute_tank_volume_with_heads(
                    fill_height,
                    self._tank_diameter,
                    cylinder_length,
                    self._end_cap_type,
                )

            self._attr_native_value = percentage
        except (ValueError, TypeError):
            _LOGGER.warning("Unable to parse source entity state '%s' as a number", state_value)
            self._attr_native_value = None
            self._fill_height = None
