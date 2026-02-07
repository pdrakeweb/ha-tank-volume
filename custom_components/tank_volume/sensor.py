"""Tank Volume Calculator sensor platform."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, PERCENTAGE
from homeassistant.const import UnitOfTemperature
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_CYLINDER_LENGTH,
    CONF_END_CAP_TYPE,
    CONF_SOURCE_ENTITY,
    CONF_TANK_DIAMETER,
    CONF_TEMPERATURE_ENTITY,
    DEFAULT_REFERENCE_TEMP_C,
    DEFAULT_REFERENCE_TEMP_F,
    DOMAIN,
    END_CAP_ELLIPSOIDAL_2_1,
    END_CAP_FLAT,
    TEMP_EXPANSION_COEFF_C,
    TEMP_EXPANSION_COEFF_F,
)

_LOGGER = logging.getLogger(__name__)


def apply_temperature_compensation(
    volume_percentage: float,
    temperature: float,
    temperature_unit: str,
) -> float:
    """
    Apply temperature compensation to volume percentage.
    
    Converts volume measured at a specific temperature to the equivalent volume
    at the reference temperature using inverse volumetric thermal expansion.
    
    Formula: V_ref = V_measured / [1 + β × (T_measured - T_ref)]
    
    This accounts for the fact that liquids expand when heated and contract when
    cooled. The measured volume at a higher temperature represents a smaller volume
    at the reference temperature, and vice versa.
    
    Args:
        volume_percentage: The calculated volume percentage at measured temperature
        temperature: Current temperature of the liquid
        temperature_unit: Unit of temperature (UnitOfTemperature.CELSIUS or FAHRENHEIT)
    
    Returns:
        Adjusted volume percentage at reference temperature (60°F/15°C)
    """
    # Determine coefficient and reference temperature based on unit
    if temperature_unit == UnitOfTemperature.CELSIUS:
        beta = TEMP_EXPANSION_COEFF_C
        reference_temp = DEFAULT_REFERENCE_TEMP_C
    else:  # Default to Fahrenheit
        beta = TEMP_EXPANSION_COEFF_F
        reference_temp = DEFAULT_REFERENCE_TEMP_F
    
    # Calculate temperature difference from reference
    temp_diff = temperature - reference_temp
    
    # Apply compensation factor
    # Volume at measured temp = Volume at reference × [1 + β × ΔT]
    # So: Volume at reference = Volume at measured temp / [1 + β × ΔT]
    compensation_factor = 1.0 / (1.0 + beta * temp_diff)
    
    return volume_percentage * compensation_factor


def compute_horizontal_cylinder_volume_percentage(
    fill_height_inches: float, diameter_inches: float
) -> float | None:
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

        # Calculate percentage
        percentage = (segment_area / circle_area) * 100.0

        return percentage
    except (ValueError, ZeroDivisionError):
        return None


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

    h = fill_height
    r = radius
    a = head_depth

    # V = (π × a / (3 × r²)) × h² × (3r - h)
    volume = (math.pi * a / (3.0 * r * r)) * h * h * (3.0 * r - h)
    return volume


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

        # Calculate percentage
        percentage = (total_volume / total_capacity) * 100.0

        return percentage
    except (ValueError, ZeroDivisionError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tank Volume Calculator sensor from a config entry."""
    source_entity = config_entry.data[CONF_SOURCE_ENTITY]
    tank_diameter = config_entry.options.get(
        CONF_TANK_DIAMETER, config_entry.data[CONF_TANK_DIAMETER]
    )
    name = config_entry.data[CONF_NAME]

    # Get end cap configuration
    end_cap_type = config_entry.options.get(
        CONF_END_CAP_TYPE, config_entry.data.get(CONF_END_CAP_TYPE, END_CAP_ELLIPSOIDAL_2_1)
    )
    cylinder_length = config_entry.options.get(
        CONF_CYLINDER_LENGTH, config_entry.data.get(CONF_CYLINDER_LENGTH)
    )
    
    # Get temperature entity (optional)
    temperature_entity = config_entry.options.get(
        CONF_TEMPERATURE_ENTITY, config_entry.data.get(CONF_TEMPERATURE_ENTITY)
    )

    sensor = TankVolumeSensor(
        config_entry.entry_id,
        name,
        source_entity,
        tank_diameter,
        end_cap_type,
        cylinder_length,
        temperature_entity,
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
        temperature_entity: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._attr_name = name
        self._source_entity = source_entity
        self._tank_diameter = tank_diameter
        self._end_cap_type = end_cap_type
        self._cylinder_length = cylinder_length
        self._temperature_entity = temperature_entity
        self._fill_height: float | None = None
        self._temperature: float | None = None
        self._temperature_unit: str | None = None
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
        if self._temperature_entity:
            attrs["temperature_entity"] = self._temperature_entity
            if self._temperature is not None:
                attrs["temperature"] = self._temperature
                if self._temperature_unit:
                    attrs["temperature_unit"] = self._temperature_unit
        return attrs

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()

        # Read current state of source entity
        if (state := self.hass.states.get(self._source_entity)) is not None:
            self._handle_source_state(state.state)

        # Track state changes
        track_entities = [self._source_entity]
        
        # Read temperature entity if configured
        if self._temperature_entity:
            track_entities.append(self._temperature_entity)
            if (temp_state := self.hass.states.get(self._temperature_entity)) is not None:
                self._handle_temperature_state(temp_state)
        
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, track_entities, self._async_source_changed
            )
        )

    @callback
    def _async_source_changed(self, event: Event) -> None:
        """Handle source entity state changes."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        entity_id = new_state.entity_id
        
        # Handle source entity changes
        if entity_id == self._source_entity:
            self._handle_source_state(new_state.state)
        # Handle temperature entity changes
        elif entity_id == self._temperature_entity:
            self._handle_temperature_state(new_state)
            
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
                percentage = compute_horizontal_cylinder_volume_percentage(
                    fill_height, self._tank_diameter
                )
            else:
                # Use cylinder length for tank with ellipsoidal heads
                cylinder_length = self._cylinder_length or self._tank_diameter
                percentage = compute_tank_volume_with_heads(
                    fill_height,
                    self._tank_diameter,
                    cylinder_length,
                    self._end_cap_type,
                )

            # Apply temperature compensation if configured and available
            if (
                percentage is not None
                and self._temperature_entity
                and self._temperature is not None
                and self._temperature_unit is not None
            ):
                percentage = apply_temperature_compensation(
                    percentage, self._temperature, self._temperature_unit
                )

            self._attr_native_value = percentage
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Unable to parse source entity state '%s' as a number", state_value
            )
            self._attr_native_value = None
            self._fill_height = None

    def _handle_temperature_state(self, state: Any) -> None:
        """Handle temperature entity state."""
        # Handle unavailable or unknown states
        if state.state in ("unknown", "unavailable", None):
            self._temperature = None
            self._temperature_unit = None
            return

        # Try to parse temperature
        try:
            self._temperature = float(state.state)
            # Get the unit of measurement from the state attributes
            self._temperature_unit = state.attributes.get("unit_of_measurement")
            
            # Validate unit - if unsupported, disable temperature compensation
            if self._temperature_unit not in (
                UnitOfTemperature.CELSIUS,
                UnitOfTemperature.FAHRENHEIT,
            ):
                _LOGGER.warning(
                    "Temperature entity has unsupported unit '%s', expected C or F. "
                    "Temperature compensation will be disabled.",
                    self._temperature_unit,
                )
                self._temperature = None
                self._temperature_unit = None
                return
                
            # Recalculate volume with new temperature if we have fill height
            if self._fill_height is not None:
                # Trigger recalculation by calling handler with current fill height
                self._handle_source_state(str(self._fill_height))
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Unable to parse temperature entity state '%s' as a number", state.state
            )
            self._temperature = None
            self._temperature_unit = None
