"""Constants for eHome EMS."""
DOMAIN = "ehome_ems"
VERSION = "0.2.12"
CONF_GRID_POWER = "grid_power"
CONF_GRID_IMPORT = "grid_import"
CONF_GRID_EXPORT = "grid_export"
CONF_SOLAR_POWER = "solar_power"
CONF_HOME_POWER = "home_power"
SOURCES = (CONF_GRID_POWER, CONF_GRID_IMPORT, CONF_GRID_EXPORT, CONF_SOLAR_POWER, CONF_HOME_POWER)
CONF_BATTERIES = "batteries"
BATTERY_SOURCES = ("charge_power", "discharge_power", "soc", "remaining_energy")
HOME_MODE = "home_power_mode"
HOME_SETTINGS = (HOME_MODE, "home_has_solar", "home_has_storage", "home_boundary_confirmed",
                 "home_max_age_seconds", "home_grid_mode", "home_freshness_policy")
CONF_USAGES = "usages"
USAGE_SOURCES = ("power", "energy", "status", "temperature")
DAILY_SOURCES = ("solar", "home", "import", "export", "charge", "discharge")
