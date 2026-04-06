"""Auto-create Lovelace dashboard for Heatpump Energy Monitor."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DASHBOARD_URL_PATH = "heatpump-energy"


def _build_entity_id(entry_id: str, key: str) -> str:
    """Build the expected entity_id for a sensor key."""
    # HA generates: sensor.<device_name_slug>_<sensor_name_slug>
    # Device name is "Wärmepumpen-Energiemonitor", sensor names start with "WP ..."
    # But with has_entity_name=True, HA uses: sensor.<device_slug>_<name_slug>
    # We use unique_id based lookup instead - HA slugifies the name
    # Format: sensor.warmepumpen_energiemonitor_wp_<rest>
    prefix = "sensor.warmepumpen_energiemonitor_"
    key_map = {
        "hp_total_power": "wp_gesamtleistung",
        "hp_heat_power": "wp_heizung_leistung",
        "hp_dhw_power": "wp_warmwasser_leistung",
        "hp_heat_from_pv": "wp_heizung_aus_pv",
        "hp_heat_from_grid": "wp_heizung_aus_netz",
        "hp_dhw_from_pv": "wp_warmwasser_aus_pv",
        "hp_dhw_from_grid": "wp_warmwasser_aus_netz",
        "pv_share_percent": "wp_pv_anteil",
        "energy_total": "wp_gesamtenergie",
        "energy_heat_total": "wp_heizung_energie",
        "energy_dhw_total": "wp_warmwasser_energie",
        "energy_from_pv": "wp_energie_aus_pv",
        "energy_from_grid": "wp_energie_aus_netz",
        "energy_heat_from_pv": "wp_heizung_energie_aus_pv",
        "energy_heat_from_grid": "wp_heizung_energie_aus_netz",
        "energy_dhw_from_pv": "wp_warmwasser_energie_aus_pv",
        "energy_dhw_from_grid": "wp_warmwasser_energie_aus_netz",
        "cost_total": "wp_gesamtkosten",
        "cost_heat": "wp_heizung_kosten",
        "cost_dhw": "wp_warmwasser_kosten",
        "savings_pv": "wp_ersparnis_durch_pv",
    }
    return prefix + key_map.get(key, key)


def _e(key: str) -> str:
    """Shortcut for entity ID."""
    return _build_entity_id("", key)


def _build_dashboard_config() -> dict[str, Any]:
    """Build the full Lovelace dashboard config."""
    return {
        "views": [
            {
                "title": "Wärmepumpe",
                "path": "waermepumpe",
                "cards": [
                    # ── Row 1: Gauges ──
                    {
                        "type": "horizontal-stack",
                        "cards": [
                            {
                                "type": "gauge",
                                "entity": _e("pv_share_percent"),
                                "name": "PV-Anteil",
                                "min": 0,
                                "max": 100,
                                "severity": {
                                    "green": 60,
                                    "yellow": 30,
                                    "red": 0,
                                },
                                "needle": True,
                            },
                            {
                                "type": "entity",
                                "entity": _e("hp_total_power"),
                                "name": "WP Leistung",
                                "icon": "mdi:heat-pump",
                            },
                            {
                                "type": "entity",
                                "entity": _e("cost_total"),
                                "name": "Kosten Netz",
                                "icon": "mdi:currency-eur",
                            },
                            {
                                "type": "entity",
                                "entity": _e("savings_pv"),
                                "name": "Ersparnis PV",
                                "icon": "mdi:piggy-bank",
                            },
                        ],
                    },
                    # ── Row 2: Power history ──
                    {
                        "type": "history-graph",
                        "title": "WP Leistung (24h)",
                        "hours_to_show": 24,
                        "entities": [
                            {"entity": _e("hp_heat_power"), "name": "Heizung"},
                            {"entity": _e("hp_dhw_power"), "name": "Warmwasser"},
                        ],
                    },
                    # ── Row 3: PV vs Grid power ──
                    {
                        "type": "history-graph",
                        "title": "Energiequelle (24h)",
                        "hours_to_show": 24,
                        "entities": [
                            {"entity": _e("hp_heat_from_pv"), "name": "Heizung PV"},
                            {"entity": _e("hp_heat_from_grid"), "name": "Heizung Netz"},
                            {"entity": _e("hp_dhw_from_pv"), "name": "WW PV"},
                            {"entity": _e("hp_dhw_from_grid"), "name": "WW Netz"},
                        ],
                    },
                    # ── Row 4: Daily energy bar charts ──
                    {
                        "type": "horizontal-stack",
                        "cards": [
                            {
                                "type": "statistics-graph",
                                "title": "Energie: PV vs. Netz",
                                "period": "day",
                                "stat_types": ["change"],
                                "chart_type": "bar",
                                "entities": [
                                    {"entity": _e("energy_from_pv"), "name": "PV"},
                                    {"entity": _e("energy_from_grid"), "name": "Netz"},
                                ],
                            },
                            {
                                "type": "statistics-graph",
                                "title": "Heizung vs. Warmwasser",
                                "period": "day",
                                "stat_types": ["change"],
                                "chart_type": "bar",
                                "entities": [
                                    {"entity": _e("energy_heat_total"), "name": "Heizung"},
                                    {"entity": _e("energy_dhw_total"), "name": "Warmwasser"},
                                ],
                            },
                        ],
                    },
                    # ── Row 5: Cost bar chart ──
                    {
                        "type": "statistics-graph",
                        "title": "Kosten & Ersparnis pro Tag",
                        "period": "day",
                        "stat_types": ["change"],
                        "chart_type": "bar",
                        "entities": [
                            {"entity": _e("cost_total"), "name": "Stromkosten"},
                            {"entity": _e("savings_pv"), "name": "PV-Ersparnis"},
                        ],
                    },
                    # ── Row 6: Detail tables ──
                    {
                        "type": "horizontal-stack",
                        "cards": [
                            {
                                "type": "entities",
                                "title": "Leistung (W)",
                                "entities": [
                                    {"entity": _e("hp_total_power"), "name": "Gesamt"},
                                    {"entity": _e("hp_heat_power"), "name": "Heizung"},
                                    {"entity": _e("hp_dhw_power"), "name": "Warmwasser"},
                                    {"type": "divider"},
                                    {"entity": _e("hp_heat_from_pv"), "name": "Heizung PV"},
                                    {"entity": _e("hp_heat_from_grid"), "name": "Heizung Netz"},
                                    {"entity": _e("hp_dhw_from_pv"), "name": "WW PV"},
                                    {"entity": _e("hp_dhw_from_grid"), "name": "WW Netz"},
                                ],
                            },
                            {
                                "type": "entities",
                                "title": "Energie (kWh)",
                                "entities": [
                                    {"entity": _e("energy_total"), "name": "Gesamt"},
                                    {"entity": _e("energy_heat_total"), "name": "Heizung"},
                                    {"entity": _e("energy_dhw_total"), "name": "Warmwasser"},
                                    {"type": "divider"},
                                    {"entity": _e("energy_from_pv"), "name": "aus PV"},
                                    {"entity": _e("energy_from_grid"), "name": "aus Netz"},
                                ],
                            },
                            {
                                "type": "entities",
                                "title": "Kosten (EUR)",
                                "entities": [
                                    {"entity": _e("cost_total"), "name": "Gesamt"},
                                    {"entity": _e("cost_heat"), "name": "Heizung"},
                                    {"entity": _e("cost_dhw"), "name": "Warmwasser"},
                                    {"type": "divider"},
                                    {"entity": _e("savings_pv"), "name": "Ersparnis PV"},
                                ],
                            },
                        ],
                    },
                ],
            }
        ]
    }


async def async_create_dashboard(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Create the WP energy dashboard automatically."""
    try:
        lovelace_data = hass.data.get("lovelace")
        if not lovelace_data:
            _LOGGER.debug("Lovelace not available, skipping dashboard creation")
            return

        dashboards = lovelace_data.get("dashboards", {})

        # Dashboard already exists
        if DASHBOARD_URL_PATH in dashboards:
            _LOGGER.debug("Dashboard '%s' already exists", DASHBOARD_URL_PATH)
            return

        # Create the dashboard entry
        collection = lovelace_data.get("dashboards_collection")
        if not collection:
            _LOGGER.debug("No dashboards_collection, skipping dashboard creation")
            return

        await collection.async_create_item(
            {
                "url_path": DASHBOARD_URL_PATH,
                "title": "WP Energie",
                "icon": "mdi:heat-pump",
                "show_in_sidebar": True,
                "require_admin": False,
                "mode": "storage",
            }
        )

        _LOGGER.info("Created dashboard '%s'", DASHBOARD_URL_PATH)

        # Now save the dashboard content
        dashboard_obj = lovelace_data["dashboards"].get(DASHBOARD_URL_PATH)
        if dashboard_obj and hasattr(dashboard_obj, "async_save"):
            await dashboard_obj.async_save(_build_dashboard_config())
            _LOGGER.info("Saved dashboard config for '%s'", DASHBOARD_URL_PATH)

    except Exception:
        _LOGGER.warning(
            "Could not auto-create dashboard. You can manually create it "
            "using the YAML from dashboard/heatpump_energy_dashboard.yaml",
            exc_info=True,
        )
