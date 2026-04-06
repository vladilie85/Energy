"""Constants for the Heatpump Energy Monitor integration."""

DOMAIN = "heatpump_energy_monitor"

# Config keys
CONF_PV_POWER = "pv_power_entity"
CONF_GRID_POWER = "grid_power_entity"
CONF_HP_HEAT_POWER = "hp_heat_power_entity"
CONF_HP_DHW_POWER = "hp_dhw_power_entity"
CONF_GRID_POSITIVE_IMPORT = "grid_positive_import"
CONF_ELECTRICITY_PRICE = "electricity_price"

# Defaults
DEFAULT_ELECTRICITY_PRICE = 30.0  # ct/kWh
DEFAULT_GRID_POSITIVE_IMPORT = True
