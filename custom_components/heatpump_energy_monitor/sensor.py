"""Sensor platform for Heatpump Energy Monitor."""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import EnergyData, HeatpumpEnergyCoordinator

_LOGGER = logging.getLogger(__name__)

POWER_SENSORS = [
    {
        "key": "hp_total_power",
        "name": "WP Gesamtleistung",
        "icon": "mdi:heat-pump",
    },
    {
        "key": "hp_heat_power",
        "name": "WP Heizung Leistung",
        "icon": "mdi:radiator",
    },
    {
        "key": "hp_dhw_power",
        "name": "WP Warmwasser Leistung",
        "icon": "mdi:water-boiler",
    },
    {
        "key": "hp_heat_from_pv",
        "name": "WP Heizung aus PV",
        "icon": "mdi:solar-power",
    },
    {
        "key": "hp_heat_from_grid",
        "name": "WP Heizung aus Netz",
        "icon": "mdi:transmission-tower",
    },
    {
        "key": "hp_dhw_from_pv",
        "name": "WP Warmwasser aus PV",
        "icon": "mdi:solar-power",
    },
    {
        "key": "hp_dhw_from_grid",
        "name": "WP Warmwasser aus Netz",
        "icon": "mdi:transmission-tower",
    },
]

ENERGY_SENSORS = [
    {
        "key": "energy_total",
        "name": "WP Gesamtenergie",
        "icon": "mdi:heat-pump",
    },
    {
        "key": "energy_heat_total",
        "name": "WP Heizung Energie",
        "icon": "mdi:radiator",
    },
    {
        "key": "energy_dhw_total",
        "name": "WP Warmwasser Energie",
        "icon": "mdi:water-boiler",
    },
    {
        "key": "energy_from_pv",
        "name": "WP Energie aus PV",
        "icon": "mdi:solar-power",
    },
    {
        "key": "energy_from_grid",
        "name": "WP Energie aus Netz",
        "icon": "mdi:transmission-tower",
    },
    {
        "key": "energy_heat_from_pv",
        "name": "WP Heizung Energie aus PV",
        "icon": "mdi:solar-power",
    },
    {
        "key": "energy_heat_from_grid",
        "name": "WP Heizung Energie aus Netz",
        "icon": "mdi:transmission-tower",
    },
    {
        "key": "energy_dhw_from_pv",
        "name": "WP Warmwasser Energie aus PV",
        "icon": "mdi:solar-power",
    },
    {
        "key": "energy_dhw_from_grid",
        "name": "WP Warmwasser Energie aus Netz",
        "icon": "mdi:transmission-tower",
    },
]

COST_SENSORS = [
    {
        "key": "cost_total",
        "name": "WP Gesamtkosten",
        "icon": "mdi:currency-eur",
    },
    {
        "key": "cost_heat",
        "name": "WP Heizung Kosten",
        "icon": "mdi:currency-eur",
    },
    {
        "key": "cost_dhw",
        "name": "WP Warmwasser Kosten",
        "icon": "mdi:currency-eur",
    },
    {
        "key": "savings_pv",
        "name": "WP Ersparnis durch PV",
        "icon": "mdi:piggy-bank",
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator: HeatpumpEnergyCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SensorEntity] = []

    for sensor_def in POWER_SENSORS:
        entities.append(
            HeatpumpPowerSensor(coordinator, config_entry, sensor_def)
        )

    for sensor_def in ENERGY_SENSORS:
        entities.append(
            HeatpumpEnergySensor(coordinator, config_entry, sensor_def)
        )

    for sensor_def in COST_SENSORS:
        entities.append(
            HeatpumpCostSensor(coordinator, config_entry, sensor_def)
        )

    entities.append(
        HeatpumpPercentSensor(
            coordinator,
            config_entry,
            {
                "key": "pv_share_percent",
                "name": "WP PV-Anteil",
                "icon": "mdi:solar-power-variant",
            },
        )
    )

    async_add_entities(entities)


class HeatpumpBaseSensor(RestoreEntity, SensorEntity):
    """Base sensor for Heatpump Energy Monitor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HeatpumpEnergyCoordinator,
        config_entry: ConfigEntry,
        sensor_def: dict,
    ) -> None:
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._key = sensor_def["key"]
        self._attr_name = sensor_def["name"]
        self._attr_icon = sensor_def["icon"]
        self._attr_unique_id = f"{config_entry.entry_id}_{self._key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Wärmepumpen-Energiemonitor",
            "manufacturer": "Custom",
            "model": "Energy Monitor",
        }

    async def async_added_to_hass(self) -> None:
        """Register listener when added to hass."""
        await super().async_added_to_hass()
        self._coordinator.register_listener(self._handle_coordinator_update)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class HeatpumpPowerSensor(HeatpumpBaseSensor):
    """Sensor for instantaneous power values (W)."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_suggested_display_precision = 0

    @property
    def native_value(self) -> float:
        """Return the current power value."""
        return round(getattr(self._coordinator.data, self._key, 0.0), 1)


class HeatpumpEnergySensor(HeatpumpBaseSensor):
    """Sensor for cumulative energy values (kWh)."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 2

    async def async_added_to_hass(self) -> None:
        """Restore previous state on startup."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in ("unknown", "unavailable"):
            try:
                restored_value = float(last_state.state)
                setattr(self._coordinator.data, self._key, restored_value)
            except (ValueError, TypeError):
                pass

    @property
    def native_value(self) -> float:
        """Return the cumulative energy value."""
        return round(getattr(self._coordinator.data, self._key, 0.0), 3)


class HeatpumpCostSensor(HeatpumpBaseSensor):
    """Sensor for cumulative cost values (EUR)."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "EUR"
    _attr_suggested_display_precision = 2

    async def async_added_to_hass(self) -> None:
        """Restore previous state on startup."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in ("unknown", "unavailable"):
            try:
                restored_value = float(last_state.state)
                setattr(self._coordinator.data, self._key, restored_value)
            except (ValueError, TypeError):
                pass

    @property
    def native_value(self) -> float:
        """Return the cumulative cost value."""
        return round(getattr(self._coordinator.data, self._key, 0.0), 2)


class HeatpumpPercentSensor(HeatpumpBaseSensor):
    """Sensor for percentage values (%)."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"
    _attr_suggested_display_precision = 0

    @property
    def native_value(self) -> float:
        """Return the percentage value."""
        return round(getattr(self._coordinator.data, self._key, 0.0), 1)
