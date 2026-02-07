"""Constants for the Tank Volume Calculator integration."""

DOMAIN = "tank_volume"

# Configuration keys
CONF_SOURCE_ENTITY = "source_entity"
CONF_TANK_DIAMETER = "tank_diameter"
CONF_NAME = "name"
CONF_END_CAP_TYPE = "end_cap_type"
CONF_END_CAP_DEPTH = "end_cap_depth"
CONF_CYLINDER_LENGTH = "cylinder_length"

# End cap types
END_CAP_FLAT = "flat"
END_CAP_ELLIPSOIDAL_2_1 = "ellipsoidal_2_1"
END_CAP_ELLIPSOIDAL_CUSTOM = "ellipsoidal_custom"

# Defaults
DEFAULT_NAME = "Tank Volume"
DEFAULT_END_CAP_TYPE = END_CAP_FLAT  # Backward compatible

# Platforms
PLATFORMS = ["sensor"]
