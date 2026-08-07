"""Switch proxies for source control entities (opt-in)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DEVICE_HUB,
    DEVICE_NAMES,
    DOMAIN,
    ENTITY_PREFIX,
    SIGNAL_CONTROLS_CHANGED,
)
from .coordinator import HubCoordinator
from .mapping import CONTROL_DEFS_BY_KEY, HubControlDef


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HubCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HubSwitchProxy(coordinator, CONTROL_DEFS_BY_KEY[key])
        for key in coordinator.control_candidates
        if CONTROL_DEFS_BY_KEY[key].platform == "switch"
    )


class HubControlProxyBase:
    """Shared logic: mirror the first available source entity."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HubCoordinator,
        control_def: HubControlDef,
    ) -> None:
        self._coordinator = coordinator
        self._def = control_def
        self._unsub_sources = None
        self._attr_unique_id = f"{ENTITY_PREFIX}_{control_def.key}"
        self.entity_id = f"{control_def.platform}.{ENTITY_PREFIX}_{control_def.key}"
        self._attr_translation_key = control_def.key
        self._attr_icon = control_def.icon
        device = control_def.device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device)},
            name=DEVICE_NAMES[device],
            manufacturer="naked-head",
            entry_type=DeviceEntryType.SERVICE,
            via_device=(DOMAIN, DEVICE_HUB),
        )

    @property
    def _sources(self) -> dict[str, str]:
        """Live view of the coordinator mapping for this control.

        Read through the coordinator instead of caching the dict handed
        over at construction time: `discover()` rebuilds
        `control_candidates` from scratch on every rediscovery, so a
        cached reference would keep pointing at pre-rename entity ids.
        """
        return self._coordinator.control_candidates.get(self._def.key, {})

    def _source_entity_id(self) -> str | None:
        """First source in priority order with a valid state."""
        sources = self._sources
        for source in self._coordinator.priority:
            entity_id = sources.get(source)
            if not entity_id:
                continue
            state = self.hass.states.get(entity_id)
            if state and state.state not in ("unavailable", "unknown"):
                return entity_id
        return None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._resubscribe_sources()
        self.async_on_remove(self._unsubscribe_sources)
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_CONTROLS_CHANGED}_{self._coordinator.entry.entry_id}",
                self._handle_controls_changed,
            )
        )

    @callback
    def _unsubscribe_sources(self) -> None:
        if self._unsub_sources:
            self._unsub_sources()
            self._unsub_sources = None

    @callback
    def _resubscribe_sources(self) -> None:
        self._unsubscribe_sources()
        tracked = sorted(set(self._sources.values()))
        if tracked:
            self._unsub_sources = async_track_state_change_event(
                self.hass, tracked, self._on_source_change
            )

    @callback
    def _handle_controls_changed(self) -> None:
        """Rediscovery moved this control: follow it to its new entity ids."""
        self._resubscribe_sources()
        self.async_write_ha_state()

    @callback
    def _on_source_change(self, _event) -> None:
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self._source_entity_id() is not None

    @property
    def extra_state_attributes(self):
        return {"source_entity": self._source_entity_id()}


class HubSwitchProxy(HubControlProxyBase, SwitchEntity):
    @property
    def is_on(self) -> bool | None:
        entity_id = self._source_entity_id()
        if not entity_id:
            return None
        return self.hass.states.get(entity_id).state == STATE_ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._call("turn_on")

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._call("turn_off")

    async def _call(self, service: str) -> None:
        entity_id = self._source_entity_id()
        if entity_id:
            await self.hass.services.async_call(
                "switch", service, {"entity_id": entity_id}, blocking=True
            )
