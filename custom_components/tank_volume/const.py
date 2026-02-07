"""Constants for the Tank Volume Calculator integration."""

DOMAIN = "tank_volume"

# Configuration keys
CONF_SOURCE_ENTITY = "source_entity"
CONF_TANK_DIAMETER = "tank_diameter"
CONF_NAME = "name"
CONF_END_CAP_TYPE = "end_cap_type"
CONF_END_CAP_DEPTH = "end_cap_depth"
CONF_CYLINDER_LENGTH = "cylinder_length"
CONF_TANK_CAPACITY = "tank_capacity"

# End cap types
END_CAP_FLAT = "flat"
END_CAP_ELLIPSOIDAL_2_1 = "ellipsoidal_2_1"

# Tank capacity presets (in gallons)
CAPACITY_250 = "250"
CAPACITY_330 = "330"
CAPACITY_500 = "500"
CAPACITY_1000 = "1000"
CAPACITY_CUSTOM = "custom"

# Standard tank specifications (diameter in inches, total length in inches)
TANK_SPECS = {
    CAPACITY_250: {"diameter": 30, "total_length": 92},
    CAPACITY_330: {"diameter": 30, "total_length": 120},
    CAPACITY_500: {"diameter": 37.5, "total_length": 120},
    CAPACITY_1000: {"diameter": 41, "total_length": 190},
}

# Defaults
DEFAULT_NAME = "Tank Volume"
DEFAULT_END_CAP_TYPE = END_CAP_ELLIPSOIDAL_2_1  # Most common for LP tanks
DEFAULT_TANK_CAPACITY = CAPACITY_500

# Platforms
PLATFORMS = ["sensor"]
