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
CONF_TEMPERATURE_LAG_HOURS = "temperature_lag_hours"
CONF_TEMPERATURE_LAG_PER_DEGREE = "temperature_lag_per_degree"
CONF_TEMPERATURE_SMOOTHING_HOURS = "temperature_smoothing_hours"

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
# Wikipedia indicates an expansion coefficient of around 0.0015 per degree F for propane.
# Fitting a full year of Mopeka Pro tank data (4-84 F, a wide range of fill levels) against
# the daily temperature swing gives an effective coefficient of about 0.0022 per degree F for
# the reported (ultrasonic) volume, which is what we use as the default. The effective
# coefficient is essentially flat with temperature for this sensor (the ultrasonic speed-of-
# sound response offsets propane's rising liquid expansion), so a fixed value is used.
PROPANE_EXPANSION_COEFFICIENT_F = 0.0022

DEFAULT_ADJUSTMENT_COEFFICIENT = PROPANE_EXPANSION_COEFFICIENT_F

# Temperature transport-lag compensation.
# The liquid's *bulk* temperature (which drives volumetric expansion) is a delayed,
# low-passed version of the measured sensor temperature because of the liquid's thermal
# mass (an externally clamped sensor tracks the tank skin/ambient, which leads the bulk).
# Compensating against the instantaneous reading corrects at the wrong phase and can amplify
# the daily swing. A full year of tank data shows the lead is strongly temperature dependent
# and (once temperature is controlled) independent of fill level:
#     lag_hours ~= DEFAULT_TEMPERATURE_LAG_HOURS + DEFAULT_TEMPERATURE_LAG_PER_DEGREE*(T - 60F)
# i.e. ~2-3 h in cold weather and ~6-7 h when warm. Set the per-degree slope to 0 for a
# constant lag, and the lag to 0 for the legacy instantaneous behaviour.
DEFAULT_TEMPERATURE_LAG_HOURS = 5.0  # transport lag (hours) at the 60 F reference temperature
DEFAULT_TEMPERATURE_LAG_PER_DEGREE = 0.067  # additional hours of lag per degree F above 60 F
DEFAULT_TEMPERATURE_SMOOTHING_HOURS = 1.0
# Bounds applied to the temperature-dependent lag.
MIN_TEMPERATURE_LAG_HOURS = 1.0
MAX_TEMPERATURE_LAG_HOURS = 12.0
# Time constant (hours) of the slow temperature average used to pick the lag, so the lag
# tracks the season rather than the daily cycle.
TEMPERATURE_LAG_SEASON_TIME_CONSTANT_HOURS = 24.0

# Platforms
PLATFORMS = ["sensor"]
