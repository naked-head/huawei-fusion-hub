"""Select proxies for source control entities (opt-in)."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
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
        HubSelectProxy(coordinator, CONTROL_DEFS_BY_KEY[key])
        for key in coordinator.control_candidates
        if CONTROL_DEFS_BY_KEY[key].platform == "select"
    )


class HubSelectProxy(HubControlProxyBase, SelectEntity):
    @property
    def options(self) -> list[str]:
        entity_id = self._source_entity_id()
        if not entity_id:
            return []
        return self.hass.states.get(entity_id).attributes.get("options", [])

    @property
    def current_option(self) -> str | None:
        entity_id = self._source_entity_id()
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id).state
        return state if state in self.options else None

    async def async_select_option(self, option: str) -> None:
        entity_id = self._source_entity_id()
        if entity_id:
            await self.hass.services.async_call(
                "select",
                "select_option",
                {"entity_id": entity_id, "option": option},
                blocking=True,
            )
