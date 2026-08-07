"""Button proxies for source momentary actions (opt-in)."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
        HubButtonProxy(coordinator, CONTROL_DEFS_BY_KEY[key])
        for key in coordinator.control_candidates
        if CONTROL_DEFS_BY_KEY[key].platform == "button"
    )


class HubButtonProxy(HubControlProxyBase, ButtonEntity):
    async def async_press(self) -> None:
        entity_id = self._source_entity_id()
        if entity_id:
            await self.hass.services.async_call(
                "button", "press", {"entity_id": entity_id}, blocking=True
            )
