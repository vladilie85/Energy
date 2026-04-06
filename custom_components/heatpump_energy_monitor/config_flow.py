"""Config flow for Heatpump Energy Monitor."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    BooleanSelector,
)

from .const import (
    DOMAIN,
    CONF_PV_POWER,
    CONF_GRID_POWER,
    CONF_HP_HEAT_POWER,
    CONF_HP_DHW_POWER,
    CONF_GRID_POSITIVE_IMPORT,
    CONF_ELECTRICITY_PRICE,
    DEFAULT_ELECTRICITY_PRICE,
    DEFAULT_GRID_POSITIVE_IMPORT,
)


class HeatpumpEnergyMonitorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Heatpump Energy Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Step 1: Select source entities."""
        if user_input is not None:
            self._sensor_data = user_input
            return await self.async_step_cost()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HP_HEAT_POWER): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_HP_DHW_POWER): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_PV_POWER): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_GRID_POWER): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(
                        CONF_GRID_POSITIVE_IMPORT,
                        default=DEFAULT_GRID_POSITIVE_IMPORT,
                    ): BooleanSelector(),
                }
            ),
        )

    async def async_step_cost(self, user_input=None):
        """Step 2: Set electricity price."""
        if user_input is not None:
            data = {**self._sensor_data, **user_input}
            return self.async_create_entry(
                title="Wärmepumpen-Energiemonitor",
                data=data,
            )

        return self.async_show_form(
            step_id="cost",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ELECTRICITY_PRICE,
                        default=DEFAULT_ELECTRICITY_PRICE,
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0,
                            max=100,
                            step=0.01,
                            unit_of_measurement="ct/kWh",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow."""
        return HeatpumpEnergyMonitorOptionsFlow(config_entry)


class HeatpumpEnergyMonitorOptionsFlow(OptionsFlow):
    """Handle options flow for Heatpump Energy Monitor."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_price = self.config_entry.options.get(
            CONF_ELECTRICITY_PRICE,
            self.config_entry.data.get(
                CONF_ELECTRICITY_PRICE, DEFAULT_ELECTRICITY_PRICE
            ),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ELECTRICITY_PRICE,
                        default=current_price,
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0,
                            max=100,
                            step=0.01,
                            unit_of_measurement="ct/kWh",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
