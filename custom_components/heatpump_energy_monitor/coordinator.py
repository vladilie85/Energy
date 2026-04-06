"""Data coordinator for Heatpump Energy Monitor."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

from .const import (
    CONF_PV_POWER,
    CONF_GRID_POWER,
    CONF_HP_HEAT_POWER,
    CONF_HP_DHW_POWER,
    CONF_GRID_POSITIVE_IMPORT,
    CONF_ELECTRICITY_PRICE,
    DEFAULT_ELECTRICITY_PRICE,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class EnergyData:
    """Current calculated power values (W) and cumulative energy (kWh)."""

    # Instantaneous power (W)
    hp_heat_power: float = 0.0
    hp_dhw_power: float = 0.0
    hp_total_power: float = 0.0
    hp_heat_from_pv: float = 0.0
    hp_heat_from_grid: float = 0.0
    hp_dhw_from_pv: float = 0.0
    hp_dhw_from_grid: float = 0.0

    # Cumulative energy (kWh)
    energy_heat_total: float = 0.0
    energy_dhw_total: float = 0.0
    energy_total: float = 0.0
    energy_heat_from_pv: float = 0.0
    energy_heat_from_grid: float = 0.0
    energy_dhw_from_pv: float = 0.0
    energy_dhw_from_grid: float = 0.0
    energy_from_pv: float = 0.0
    energy_from_grid: float = 0.0

    # Cost (EUR)
    cost_total: float = 0.0
    cost_heat: float = 0.0
    cost_dhw: float = 0.0
    savings_pv: float = 0.0


class HeatpumpEnergyCoordinator:
    """Coordinator that tracks heat pump energy and calculates PV/grid split."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_data: dict[str, Any],
        options: dict[str, Any],
        restored_data: EnergyData | None = None,
    ) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self._config = config_data
        self._options = options

        self._hp_heat_entity = config_data[CONF_HP_HEAT_POWER]
        self._hp_dhw_entity = config_data[CONF_HP_DHW_POWER]
        self._pv_entity = config_data[CONF_PV_POWER]
        self._grid_entity = config_data[CONF_GRID_POWER]
        self._grid_positive_import = config_data.get(CONF_GRID_POSITIVE_IMPORT, True)

        self.data = restored_data if restored_data else EnergyData()
        self._last_update: float | None = None
        self._listeners: list[callable] = []
        self._unsub: list[callable] = []

    @property
    def electricity_price(self) -> float:
        """Get current electricity price in ct/kWh."""
        return self._options.get(
            CONF_ELECTRICITY_PRICE,
            self._config.get(CONF_ELECTRICITY_PRICE, DEFAULT_ELECTRICITY_PRICE),
        )

    def update_options(self, options: dict[str, Any]) -> None:
        """Update options (e.g., electricity price changed)."""
        self._options = options

    def register_listener(self, listener: callable) -> None:
        """Register a callback to be called when data updates."""
        self._listeners.append(listener)

    def _notify_listeners(self) -> None:
        """Notify all registered listeners."""
        for listener in self._listeners:
            listener()

    def _get_float_state(self, entity_id: str) -> float | None:
        """Get a float value from an entity state."""
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    @callback
    def _handle_state_change(self, event: Event) -> None:
        """Handle state changes of source sensors."""
        now = time.monotonic()

        hp_heat = self._get_float_state(self._hp_heat_entity)
        hp_dhw = self._get_float_state(self._hp_dhw_entity)
        pv_power = self._get_float_state(self._pv_entity)
        grid_power = self._get_float_state(self._grid_entity)

        if any(v is None for v in (hp_heat, hp_dhw, pv_power, grid_power)):
            return

        hp_heat = max(0.0, hp_heat)
        hp_dhw = max(0.0, hp_dhw)
        pv_power = max(0.0, pv_power)

        # Normalize grid: positive = import, negative = export
        if not self._grid_positive_import:
            grid_power = -grid_power

        # Calculate house total consumption
        # house_total = pv_power + grid_power (grid_power positive=import, negative=export)
        house_total = pv_power + grid_power

        # PV self-consumption (what stays in the house)
        grid_export = max(0.0, -grid_power)
        pv_self_consumed = max(0.0, pv_power - grid_export)

        # Heat pump total
        hp_total = hp_heat + hp_dhw

        # Proportional PV allocation
        if house_total > 0 and hp_total > 0:
            hp_share = min(hp_total / house_total, 1.0)
            hp_from_pv_total = hp_share * pv_self_consumed
            hp_from_pv_total = min(hp_from_pv_total, hp_total)
        else:
            hp_from_pv_total = 0.0

        hp_from_grid_total = max(0.0, hp_total - hp_from_pv_total)

        # Split between heating and DHW
        if hp_total > 0:
            heat_ratio = hp_heat / hp_total
            dhw_ratio = hp_dhw / hp_total
        else:
            heat_ratio = 0.0
            dhw_ratio = 0.0

        heat_from_pv = hp_from_pv_total * heat_ratio
        heat_from_grid = hp_from_grid_total * heat_ratio
        dhw_from_pv = hp_from_pv_total * dhw_ratio
        dhw_from_grid = hp_from_grid_total * dhw_ratio

        # Update instantaneous power values
        self.data.hp_heat_power = hp_heat
        self.data.hp_dhw_power = hp_dhw
        self.data.hp_total_power = hp_total
        self.data.hp_heat_from_pv = heat_from_pv
        self.data.hp_heat_from_grid = heat_from_grid
        self.data.hp_dhw_from_pv = dhw_from_pv
        self.data.hp_dhw_from_grid = dhw_from_grid

        # Riemann integration (trapezoidal) for energy accumulation
        if self._last_update is not None:
            dt_hours = (now - self._last_update) / 3600.0

            if dt_hours > 0 and dt_hours < 1.0:  # Skip unreasonable gaps
                # Convert W to kWh: power(W) * time(h) / 1000
                self.data.energy_heat_total += hp_heat * dt_hours / 1000.0
                self.data.energy_dhw_total += hp_dhw * dt_hours / 1000.0
                self.data.energy_total += hp_total * dt_hours / 1000.0
                self.data.energy_heat_from_pv += heat_from_pv * dt_hours / 1000.0
                self.data.energy_heat_from_grid += heat_from_grid * dt_hours / 1000.0
                self.data.energy_dhw_from_pv += dhw_from_pv * dt_hours / 1000.0
                self.data.energy_dhw_from_grid += dhw_from_grid * dt_hours / 1000.0
                self.data.energy_from_pv += hp_from_pv_total * dt_hours / 1000.0
                self.data.energy_from_grid += hp_from_grid_total * dt_hours / 1000.0

                # Cost calculation (ct/kWh -> EUR)
                price_eur_per_kwh = self.electricity_price / 100.0
                grid_energy_increment = hp_from_grid_total * dt_hours / 1000.0
                pv_energy_increment = hp_from_pv_total * dt_hours / 1000.0

                self.data.cost_total += grid_energy_increment * price_eur_per_kwh
                self.data.cost_heat += (
                    heat_from_grid * dt_hours / 1000.0 * price_eur_per_kwh
                )
                self.data.cost_dhw += (
                    dhw_from_grid * dt_hours / 1000.0 * price_eur_per_kwh
                )
                self.data.savings_pv += pv_energy_increment * price_eur_per_kwh

        self._last_update = now
        self._notify_listeners()

    async def async_start(self) -> None:
        """Start listening to state changes."""
        entities = [
            self._hp_heat_entity,
            self._hp_dhw_entity,
            self._pv_entity,
            self._grid_entity,
        ]
        self._unsub.append(
            async_track_state_change_event(
                self.hass, entities, self._handle_state_change
            )
        )
        _LOGGER.debug("Heatpump Energy Monitor coordinator started")

    async def async_stop(self) -> None:
        """Stop listening."""
        for unsub in self._unsub:
            unsub()
        self._unsub.clear()
