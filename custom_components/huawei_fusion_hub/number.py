"""Number proxies for source setpoint entities (opt-in)."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import HubCoordinator
from .mapping import CONTROL_DEFS_BY_KEY
from .switch import HubControlProxyBase


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HubCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HubNumberProxy(coordinator, CONTROL_DEFS_BY_KEY[key])
        for key in coordinator.control_candidates
        if CONTROL_DEFS_BY_KEY[key].platform == "number"
    )


class HubNumberProxy(HubControlProxyBase, NumberEntity):
    def _source_attr(self, attr, default=None):
        entity_id = self._source_entity_id()
        if not entity_id:
            return default
        return self.hass.states.get(entity_id).attributes.get(attr, default)

    @property
    def native_value(self) -> float | None:
        entity_id = self._source_entity_id()
        if not entity_id:
            return None
        try:
            return float(self.hass.states.get(entity_id).state)
        except (ValueError, TypeError):
            return None

    @property
    def native_min_value(self) -> float:
        return self._source_attr("min", 0)

    @property
    def native_max_value(self) -> float:
        return self._source_attr("max", 100)

    @property
    def native_step(self) -> float | None:
        return self._source_attr("step")

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._source_attr("unit_of_measurement")

    @property
    def mode(self):
        return self._source_attr("mode", "auto")

    async def async_set_native_value(self, value: float) -> None:
        entity_id = self._source_entity_id()
        if entity_id:
            await self.hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": entity_id, "value": value},
                blocking=True,
            )
