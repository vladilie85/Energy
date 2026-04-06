"""Auto-create Lovelace dashboard for Heatpump Energy Monitor."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DASHBOARD_URL_PATH = "heatpump-energy"


def _e(key: str) -> str:
    """Build entity_id for a sensor key."""
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


def _build_dashboard_config() -> dict[str, Any]:
    """Build the full Lovelace dashboard config."""
    return {
        "views": [
            {
                "title": "Wärmepumpe",
                "path": "waermepumpe",
                "cards": [
                    # Row 1: Gauges
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
                    # Row 2: Power history
                    {
                        "type": "history-graph",
                        "title": "WP Leistung (24h)",
                        "hours_to_show": 24,
                        "entities": [
                            {"entity": _e("hp_heat_power"), "name": "Heizung"},
                            {"entity": _e("hp_dhw_power"), "name": "Warmwasser"},
                        ],
                    },
                    # Row 3: PV vs Grid
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
                    # Row 4: Daily bar charts
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
                    # Row 5: Costs
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
                    # Row 6: Detail tables
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
    """Create the WP energy dashboard by writing to HA .storage."""
    storage_path = Path(hass.config.path(".storage"))

    # Check if dashboard is already registered
    dashboards_file = storage_path / "lovelace_dashboards"
    existing_dashboards: dict[str, Any] = {}

    if dashboards_file.exists():
        try:
            existing_dashboards = json.loads(dashboards_file.read_text())
        except (json.JSONDecodeError, OSError):
            _LOGGER.warning("Could not read lovelace_dashboards file")
            return

    # Check if our dashboard already exists
    items = existing_dashboards.get("data", {}).get("items", [])
    for item in items:
        if item.get("url_path") == DASHBOARD_URL_PATH:
            _LOGGER.info("Dashboard '%s' already exists", DASHBOARD_URL_PATH)
            return

    # Add our dashboard to the registry
    items.append(
        {
            "icon": "mdi:heat-pump",
            "id": DASHBOARD_URL_PATH,
            "mode": "storage",
            "require_admin": False,
            "show_in_sidebar": True,
            "title": "WP Energie",
            "url_path": DASHBOARD_URL_PATH,
        }
    )

    if not existing_dashboards:
        existing_dashboards = {
            "version": 1,
            "minor_version": 1,
            "key": "lovelace_dashboards",
            "data": {"items": items},
        }
    else:
        existing_dashboards["data"]["items"] = items

    try:
        dashboards_file.write_text(json.dumps(existing_dashboards, indent=4))
        _LOGGER.info("Registered dashboard '%s'", DASHBOARD_URL_PATH)
    except OSError:
        _LOGGER.warning("Could not write lovelace_dashboards file")
        return

    # Write the dashboard config
    config_file = storage_path / f"lovelace.{DASHBOARD_URL_PATH}"
    dashboard_storage = {
        "version": 1,
        "minor_version": 1,
        "key": f"lovelace.{DASHBOARD_URL_PATH}",
        "data": {"config": _build_dashboard_config()},
    }

    try:
        config_file.write_text(json.dumps(dashboard_storage, indent=4))
        _LOGGER.info("Saved dashboard config for '%s'", DASHBOARD_URL_PATH)
        _LOGGER.warning(
            "Dashboard 'WP Energie' wurde erstellt. "
            "Bitte Home Assistant einmal neu starten damit es in der Sidebar erscheint."
        )
    except OSError:
        _LOGGER.warning("Could not write dashboard config file")
