"""Diagnostics for Huawei Fusion Hub.

What this is for: almost every question about this integration comes down to
which source won for which canonical key, and — since the battery runtime
estimates landed — what the estimator was looking at when it produced a
number. Both are tedious to ask for one field at a time in an issue thread,
and easy to get wrong by hand.

What is left out on purpose: the values of the sensors themselves. Knowing
that the resolution picked `sensor.battery_soc` from Huawei Solar is what
makes a report actionable; knowing that it read 47% at the moment of the
download is not, and a battery SoC history is a decent proxy for whether a
house is occupied. Only the battery values the estimator actually consumes
are included, because the estimate cannot be explained without them.

Redaction: source entity IDs are kept — they are the whole point — but they
can carry a plant or site name given by the upstream integration, so a
report is still worth a glance before posting.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    KEY_BATTERY_CAPACITY,
    KEY_BATTERY_POWER,
    KEY_BATTERY_SOC,
)
from .coordinator import HubCoordinator

# Config entry fields that may carry credentials or a site identifier from the
# upstream integrations. Nothing here is needed to reproduce a resolution bug.
TO_REDACT = {
    "username",
    "password",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "plant_id",
    "station_code",
    "serial_number",
    "unique_id",
}

# The estimator's own inputs. These are values, not just entity IDs, because
# an estimate is impossible to check without them.
ESTIMATOR_INPUTS = (KEY_BATTERY_SOC, KEY_BATTERY_POWER, KEY_BATTERY_CAPACITY)


def _estimate(coordinator: HubCoordinator) -> dict[str, Any]:
    """What the estimator last produced, and what it was fed."""
    estimator = coordinator.estimator
    if estimator is None:
        return {"enabled": False}

    result = estimator.result
    inputs = {}
    for key in ESTIMATOR_INPUTS:
        resolved = (coordinator.data or {}).get(key)
        inputs[key] = {
            "value": resolved.value if resolved else None,
            "source": resolved.source if resolved else None,
            "source_entity": resolved.source_entity if resolved else None,
        }

    return {
        "enabled": True,
        "available": coordinator.derived_available,
        "reserve_soc": estimator.reserve_soc,
        "capacity_override": estimator.capacity_override,
        "inputs": inputs,
        "last_estimate": {
            "time_to_full": result.time_to_full,
            "time_to_minimum": result.time_to_minimum,
            "method": result.method,
            "confidence": result.confidence,
            "power_variation": result.power_variation,
            "capacity": result.capacity,
            "capacity_factor": result.capacity_factor,
            "samples": result.samples,
            "window_seconds": result.window_seconds,
            "source": result.source,
        },
    }


def _resolution(coordinator: HubCoordinator) -> dict[str, Any]:
    """Which source won each canonical key, and which lost.

    The winner is the one the priority order picked; the candidates are every
    source that offered an entity for that key. A key with more than one
    candidate is one where failover is actually possible.
    """
    resolved: dict[str, Any] = {}
    for key, per_source in sorted(coordinator.candidates.items()):
        current = (coordinator.data or {}).get(key)
        resolved[key] = {
            "candidates": dict(sorted(per_source.items())),
            "resolved_source": current.source if current else None,
            "resolved_entity": current.source_entity if current else None,
        }
    return resolved


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: HubCoordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        "entry": {
            # the manual overrides map canonical keys to entity IDs, which is
            # exactly what a resolution report needs: kept, not redacted
            "options": async_redact_data(dict(entry.options), TO_REDACT),
            "data": async_redact_data(dict(entry.data), TO_REDACT),
        },
        "sources": {
            "priority": list(coordinator.priority),
            "available": dict(sorted(coordinator.source_available.items())),
            "entity_counts": {
                source: len(entities)
                for source, entities in sorted(coordinator.source_entities.items())
            },
        },
        "counts": {
            "sensor_keys": len(coordinator.candidates),
            "control_keys": len(coordinator.control_candidates),
            "aggregate_controls": coordinator.aggregate_controls,
        },
        "battery_estimates": _estimate(coordinator),
        "resolution": _resolution(coordinator),
        "controls": {
            key: dict(sorted(per_source.items()))
            for key, per_source in sorted(coordinator.control_candidates.items())
        },
    }
