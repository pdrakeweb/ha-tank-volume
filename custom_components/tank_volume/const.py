"""Constants for the Tank Volume Calculator integration."""

DOMAIN = "tank_volume"

# Configuration keys
CONF_SOURCE_ENTITY = "source_entity"
CONF_TANK_DIAMETER = "tank_diameter"
CONF_TANK_TOTAL_LENGTH = "tank_total_length"
CONF_TANK_VOLUME = "tank_volume"
CONF_NAME = "name"
CONF_END_CAP_TYPE = "end_cap_type"
CONF_CYLINDER_LENGTH = "cylinder_length"
CONF_TANK_CAPACITY = "tank_capacity"
CONF_TEMPERATURE_ENTITY = "temperature_entity"
CONF_ADJUSTMENT_COEFFICIENT = "adjustment_coefficient"

# End cap types
END_CAP_FLAT = "flat"
END_CAP_ELLIPSOIDAL_2_1 = "ellipsoidal_2_1"

# Tank capacity presets (in gallons)
CAPACITY_250 = "250"
CAPACITY_325 = "325"
CAPACITY_500 = "500"
CAPACITY_1000 = "1000"
CAPACITY_CUSTOM = "custom"

# Standard tank specifications (diameter in inches, total length in inches)
TANK_SPECS = {
    CAPACITY_250: {"diameter": 30, "total_length": 92},
    CAPACITY_325: {"diameter": 30, "total_length": 120},
    CAPACITY_500: {"diameter": 37.5, "total_length": 120},
    CAPACITY_1000: {"diameter": 41, "total_length": 194},
}

# Defaults
DEFAULT_NAME = "Tank Volume"
DEFAULT_END_CAP_TYPE = END_CAP_ELLIPSOIDAL_2_1  # Most common for LP tanks
DEFAULT_TANK_CAPACITY = CAPACITY_500

# Temperature compensation constants
REFERENCE_TEMPERATURE_F = 60.0
# Wikipedia indicates an expansion coefficient of around 0.0015 per degree F for propane, which is commonly stored in these tanks.
# However, experimentally using a Mopeka Pro sensor, the expansion coefficient appears to be closer to 0.0019 per degree F, which is what we will use as the default.
PROPANE_EXPANSION_COEFFICIENT_F = 0.0019

DEFAULT_ADJUSTMENT_COEFFICIENT = PROPANE_EXPANSION_COEFFICIENT_F

# Platforms
PLATFORMS = ["sensor"]
