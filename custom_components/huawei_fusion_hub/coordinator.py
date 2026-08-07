"""Coordinator: discovers source entities, resolves values by priority."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
)
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util.unit_conversion import (
    EnergyConverter,
    PowerConverter,
    TemperatureConverter,
)

from .const import (
    CONF_AGGREGATE_CONTROLS,
    CONF_NOTIFY_ON_DISCONNECT,
    CONF_OVERRIDES,
    CONF_PRIORITY,
    CONTROL_DOMAINS,
    DEVICE_NAMES,
    DOMAIN,
    SIGNAL_CONTROLS_CHANGED,
    SIGNAL_NEW_KEYS,
    SOURCE_NAMES,
    SOURCE_OFFLINE_THRESHOLD,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .mapping import (
    CONTROL_DEFS,
    SENSOR_DEFS,
    SENSOR_DEFS_BY_KEY,
    HubSensorDef,
)
from .notifications import get_texts

_LOGGER = logging.getLogger(__name__)

BAD_STATES = ("unavailable", "unknown", None, "")


@dataclass
class ResolvedValue:
    value: Any
    source: str | None
    source_entity: str | None


@dataclass
class CandidateDiff:
    """What changed between two discovery passes.

    Kept free of Home Assistant objects so the rediscovery logic can be
    exercised directly in the test suite.
    """

    new_keys: list[str]
    gained: list[str]
    dropped: list[str]
    lost_sources: dict[str, list[str]]
    changed: bool

    @property
    def has_losses(self) -> bool:
        return bool(self.dropped or self.lost_sources)


def diff_candidates(
    old: dict[str, dict[str, str]],
    new: dict[str, dict[str, str]],
) -> CandidateDiff:
    """Compare two candidate mappings.

    `changed` is true whenever any resolved entity_id moved, including the
    case where a source entity was merely renamed: that produces no new,
    gained or dropped key, but it does invalidate the state subscriptions.
    """
    return CandidateDiff(
        new_keys=[k for k in new if k not in old],
        gained=[k for k in new if k in old and set(new[k]) - set(old[k])],
        dropped=[k for k in old if k not in new],
        lost_sources={
            k: sorted(set(old[k]) - set(new[k]))
            for k in old
            if k in new and set(old[k]) - set(new[k])
        },
        changed=old != new,
    )


class HubCoordinator(DataUpdateCoordinator[dict[str, ResolvedValue]]):
    """Event-driven coordinator over already-existing HA entities."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.entry = entry
        self.priority: list[str] = entry.options.get(
            CONF_PRIORITY, entry.data.get(CONF_PRIORITY, [])
        )
        self.notify_on_disconnect: bool = entry.options.get(
            CONF_NOTIFY_ON_DISCONNECT,
            entry.data.get(CONF_NOTIFY_ON_DISCONNECT, True),
        )
        self.aggregate_controls: bool = entry.options.get(
            CONF_AGGREGATE_CONTROLS,
            entry.data.get(CONF_AGGREGATE_CONTROLS, False),
        )
        # control_key -> {source: entity_id} (switch/select proxies)
        self.control_candidates: dict[str, dict[str, str]] = {}
        # canonical_key -> {source: entity_id}
        self.candidates: dict[str, dict[str, str]] = {}
        # source -> set of its mapped entity_ids
        self.source_entities: dict[str, set[str]] = {}
        # source -> bool (last known availability)
        self.source_available: dict[str, bool] = {}
        # sources for which an offline alert was actually fired this runtime;
        # online alerts fire only for these, so HA restarts (where sources
        # start unavailable and come up later) stay silent
        self._alerted_offline: set[str] = set()
        self._unsub = None
        self._unsub_registry = None
        self._rediscover_cancel = None
        self._store = Store(
            hass, STORAGE_VERSION, STORAGE_KEY.format(entry_id=entry.entry_id)
        )
        self._store_data: dict = {}

    # ------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------
    def discover(self) -> None:
        """Scan entity registry and resolve candidate entities per canonical key."""
        registry = er.async_get(self.hass)
        device_registry = dr.async_get(self.hass)
        overrides: dict[str, dict[str, str]] = self.entry.options.get(
            CONF_OVERRIDES, {}
        )

        # index registry entries by platform (source domain),
        # each entry paired with its device model (for FSP disambiguation)
        by_source: dict[str, list[tuple[er.RegistryEntry, str]]] = {
            s: [] for s in self.priority
        }
        for entity in registry.entities.values():
            if entity.platform in by_source and entity.domain == "sensor":
                model = ""
                if entity.device_id:
                    device = device_registry.async_get(entity.device_id)
                    if device and device.model:
                        model = device.model
                by_source[entity.platform].append((entity, model))

        self.candidates = {}
        self.source_entities = {s: set() for s in self.priority}

        for sensor_def in SENSOR_DEFS:
            per_source: dict[str, str] = {}
            for source in self.priority:
                # explicit user override wins
                override = overrides.get(sensor_def.key, {}).get(source)
                if override:
                    per_source[source] = override
                    self.source_entities[source].add(override)
                    continue
                entity_id = self._match(sensor_def, source, by_source.get(source, []))
                if entity_id:
                    per_source[source] = entity_id
                    self.source_entities[source].add(entity_id)
            if per_source:
                self.candidates[sensor_def.key] = per_source

        # --- controls (switch/select proxies), opt-in ---
        self.control_candidates = {}
        if self.aggregate_controls:
            by_source_ctl: dict[str, list[tuple[er.RegistryEntry, str]]] = {
                s: [] for s in self.priority
            }
            for entity in registry.entities.values():
                if (
                    entity.platform in by_source_ctl
                    and entity.domain in CONTROL_DOMAINS
                ):
                    model = ""
                    if entity.device_id:
                        device = device_registry.async_get(entity.device_id)
                        if device and device.model:
                            model = device.model
                    by_source_ctl[entity.platform].append((entity, model))
            for control_def in CONTROL_DEFS:
                per_source: dict[str, str] = {}
                for source in self.priority:
                    entity_id = self._match(
                        control_def, source, by_source_ctl.get(source, [])
                    )
                    if entity_id:
                        per_source[source] = entity_id
                if per_source:
                    self.control_candidates[control_def.key] = per_source

        _LOGGER.debug(
            "Discovery result: %d sensors, %d controls",
            len(self.candidates), len(self.control_candidates),
        )

    @staticmethod
    def _match(
        sensor_def: HubSensorDef,
        source: str,
        entities: list[tuple[er.RegistryEntry, str]],
    ) -> str | None:
        """Two-layer, language-independent matching.

        Layer 1 (primary): unique_id patterns from mapping.py. A pattern
        matches when the unique_id equals it or ends with "_pattern" /
        "-pattern" (case-insensitive). "Model:pattern" syntax restricts
        the match to entities whose device model equals Model (needed
        for FusionSolarPlus, which reuses numeric signal ids across
        device types). When both the definition and the registry entry
        declare a device class, they must agree.

        Layer 2 (fallback): same logic against object_ids, for older
        source versions with different unique_id schemes.
        """

        def _find(patterns: list[str], attr: str) -> str | None:
            for raw_pattern in patterns:
                if ":" in raw_pattern:
                    model_req, _, pattern = raw_pattern.partition(":")
                else:
                    model_req, pattern = None, raw_pattern
                pattern = pattern.lower()
                matches: list[tuple[int, str]] = []
                for entity, model in entities:
                    if model_req and not model.lower().startswith(model_req.lower()):
                        continue
                    if attr == "unique_id":
                        haystack = (entity.unique_id or "").lower()
                    else:
                        haystack = entity.entity_id.split(".", 1)[1].lower()
                    if not (
                        haystack == pattern
                        or haystack.endswith(f"_{pattern}")
                        or haystack.endswith(f"-{pattern}")
                    ):
                        continue
                    # device_class check removed: HA stores class as enum, string comparison unreliable
                    matches.append((len(haystack), entity.entity_id))
                if matches:
                    # shortest haystack wins: "SER_active_power" beats
                    # "SER_power_meter_active_power" for "active_power"
                    return sorted(matches)[0][1]
            return None

        result = _find(sensor_def.matchers.get(source, []), "unique_id")
        if result:
            return result
        return _find(sensor_def.fallbacks.get(source, []), "object_id")

    # ------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------
    async def async_start(self) -> None:
        # Load persisted state before the first discovery/refresh, so a
        # source that was offline before a Home Assistant restart is still
        # recognized as such: the recovery notification fires when it comes
        # back, instead of being mistaken for the silent startup transition.
        self._store_data = await self._store.async_load() or {}
        self._alerted_offline = set(self._store_data.get("alerted_offline", []))

        self.discover()
        self._subscribe_states()
        self._refresh_data()

        # rediscover when new source entities appear in the registry
        # (e.g. a source integration is installed or re-added later)
        self._unsub_registry = self.hass.bus.async_listen(
            er.EVENT_ENTITY_REGISTRY_UPDATED, self._handle_registry_event
        )

        await self._maybe_notify_initial_summary()

    async def async_stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        if self._unsub_registry:
            self._unsub_registry()
            self._unsub_registry = None
        if self._rediscover_cancel:
            self._rediscover_cancel()
            self._rediscover_cancel = None

    def _subscribe_states(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        tracked = sorted(
            {eid for sources in self.candidates.values() for eid in sources.values()}
        )
        if tracked:
            self._unsub = async_track_state_change_event(
                self.hass, tracked, self._handle_state_change
            )

    # ------------------------------------------------------------
    # Discovery notifications
    # ------------------------------------------------------------
    def _summary_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for key in self.candidates:
            device = SENSOR_DEFS_BY_KEY[key].device
            counts[device] = counts.get(device, 0) + 1
        return counts

    def _format_counts(self, counts: dict[str, int]) -> str:
        return ", ".join(
            f"{DEVICE_NAMES[device]}: {n}" for device, n in sorted(counts.items())
        )

    async def _maybe_notify_initial_summary(self) -> None:
        if self._store_data.get("summary_shown"):
            return
        per_source = {
            source: sum(
                1 for c in self.candidates.values() if source in c
            )
            for source in self.priority
        }
        source_lines = ", ".join(
            f"{SOURCE_NAMES.get(s, s)}: {n}" for s, n in per_source.items()
        )
        texts = get_texts(self.hass)
        self._notify(
            f"{DOMAIN}_summary",
            texts["summary"].format(
                total=len(self.candidates),
                counts=self._format_counts(self._summary_counts()),
                per_source=source_lines,
            ),
        )
        self._store_data["summary_shown"] = True
        await self._store.async_save(self._store_data)

    @callback
    def _handle_registry_event(self, event: Event) -> None:
        if event.data.get("action") not in ("create", "update"):
            return
        # On a rename the event carries the *new* entity_id, which is what
        # the registry lookup below needs; "update" also covers a source
        # entity being enabled, disabled or moved to another device.
        entity_id = event.data.get("entity_id", "")
        domain = entity_id.split(".", 1)[0]
        if domain != "sensor" and not (
            self.aggregate_controls and domain in CONTROL_DOMAINS
        ):
            return
        entry = er.async_get(self.hass).async_get(entity_id)
        if not entry or entry.platform not in self.priority:
            return
        # debounce: sources create dozens of entities in a burst
        if self._rediscover_cancel:
            self._rediscover_cancel()
        self._rediscover_cancel = async_call_later(
            self.hass, 10, self._async_rediscover
        )

    async def _async_rediscover(self, _now=None) -> None:
        self._rediscover_cancel = None
        old_candidates = {k: dict(v) for k, v in self.candidates.items()}
        old_controls = {k: dict(v) for k, v in self.control_candidates.items()}
        self.discover()

        diff = diff_candidates(old_candidates, self.candidates)
        new_keys = diff.new_keys
        gained = diff.gained

        # A plain entity_id rename yields no new, gained or dropped key, yet
        # it silently breaks the state listener: that listener is still
        # tracking the old ids, which will never fire again, so the hub
        # sensors freeze on their last value until the next restart.
        # Re-subscribe whenever the resolved ids changed at all, and do it
        # before any early return below.
        if diff.changed:
            self._subscribe_states()
            self._refresh_data()

        # Control proxies keep their own state subscriptions; tell them to
        # re-arm when their mapping moved.
        if self.control_candidates != old_controls:
            async_dispatcher_send(
                self.hass,
                f"{SIGNAL_CONTROLS_CHANGED}_{self.entry.entry_id}",
            )

        # Losses get no persistent notification (a source that went offline
        # is already covered by the availability alerts), but they must be
        # visible somewhere: a renamed source entity that the object_id
        # fallback layer can no longer match shows up here and nowhere else.
        if diff.dropped:
            _LOGGER.warning(
                "Rediscovery: %d key(s) no longer resolve to any source: %s",
                len(diff.dropped),
                ", ".join(sorted(diff.dropped)),
            )
        if diff.lost_sources:
            _LOGGER.warning(
                "Rediscovery: %d key(s) lost a source: %s",
                len(diff.lost_sources),
                "; ".join(
                    f"{k} ({', '.join(v)})"
                    for k, v in sorted(diff.lost_sources.items())
                ),
            )

        if not new_keys and not gained:
            return

        if new_keys:
            async_dispatcher_send(
                self.hass,
                f"{SIGNAL_NEW_KEYS}_{self.entry.entry_id}",
                new_keys,
            )

        # which sources triggered the change
        changed_sources: set[str] = set()
        for k in new_keys:
            changed_sources.update(self.candidates[k])
        for k in gained:
            changed_sources.update(
                set(self.candidates[k]) - set(old_candidates[k])
            )
        source_names = ", ".join(
            SOURCE_NAMES.get(s, s) for s in sorted(changed_sources)
        )

        texts = get_texts(self.hass)
        parts = []
        if new_keys:
            counts: dict[str, int] = {}
            for k in new_keys:
                device = SENSOR_DEFS_BY_KEY[k].device
                counts[device] = counts.get(device, 0) + 1
            parts.append(
                texts["rediscovery_new"].format(
                    n=len(new_keys), counts=self._format_counts(counts)
                )
            )
        if gained:
            parts.append(texts["rediscovery_gained"].format(n=len(gained)))
        self._notify(
            f"{DOMAIN}_rediscovery",
            texts["rediscovery"].format(
                sources=source_names, parts="; ".join(parts)
            ),
        )
        _LOGGER.info(
            "Rediscovery: %d new keys, %d gained fallback (%s)",
            len(new_keys), len(gained), source_names,
        )

    def _notify(self, notification_id: str, message: str) -> None:
        self.hass.async_create_task(
            self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "notification_id": notification_id,
                    "title": get_texts(self.hass)["title"],
                    "message": message,
                },
            )
        )

    @callback
    def _handle_state_change(self, event: Event) -> None:
        self._refresh_data()

    @callback
    def _refresh_data(self) -> None:
        data: dict[str, ResolvedValue] = {}
        for key, per_source in self.candidates.items():
            data[key] = self._resolve(key, per_source)
        self._update_source_availability()
        self.async_set_updated_data(data)

    def _resolve(self, key: str, per_source: dict[str, str]) -> ResolvedValue:
        sensor_def = SENSOR_DEFS_BY_KEY[key]
        for source in self.priority:
            entity_id = per_source.get(source)
            if not entity_id:
                continue
            state = self.hass.states.get(entity_id)
            if state is None or state.state in BAD_STATES:
                continue
            value = self._normalize(sensor_def, state)
            if value is not None:
                return ResolvedValue(value, source, entity_id)
        return ResolvedValue(None, None, None)

    @staticmethod
    def _normalize(sensor_def: HubSensorDef, state) -> Any:
        """Convert source value to the canonical unit (W, kWh, °C)."""
        raw = state.state
        try:
            value = float(raw)
        except (ValueError, TypeError):
            return raw  # non-numeric passthrough (e.g. status strings)

        src_unit = state.attributes.get("unit_of_measurement")
        dst_unit = sensor_def.unit
        if not src_unit or not dst_unit or src_unit == dst_unit:
            return value
        # reactive power is not covered by HA unit converters
        if dst_unit == "var" and src_unit in ("kvar", "kVar"):
            return round(value * 1000, 1)
        try:
            for converter in (PowerConverter, EnergyConverter, TemperatureConverter):
                if (
                    src_unit in converter.VALID_UNITS
                    and dst_unit in converter.VALID_UNITS
                ):
                    return round(converter.convert(value, src_unit, dst_unit), 3)
        except Exception:  # unit conversion is best-effort, never fatal
            _LOGGER.debug(
                "Unit conversion failed for %s: %s -> %s",
                state.entity_id,
                src_unit,
                dst_unit,
            )
        return value

    # ------------------------------------------------------------
    # Source availability + alerts
    # ------------------------------------------------------------
    def _update_source_availability(self) -> None:
        for source, entity_ids in self.source_entities.items():
            if not entity_ids:
                continue
            unavailable = 0
            for entity_id in entity_ids:
                state = self.hass.states.get(entity_id)
                if state is None or state.state in BAD_STATES:
                    unavailable += 1
            available = (unavailable / len(entity_ids)) < SOURCE_OFFLINE_THRESHOLD
            previous = self.source_available.get(source)
            self.source_available[source] = available

            if previous is True and not available:
                self._alerted_offline.add(source)
                self._persist_alerted_offline()
                self._fire_alert(source, offline=True)
            elif available and source in self._alerted_offline:
                # Recovery. previous is usually False (offline seen earlier
                # this runtime), but after a Home Assistant restart the
                # in-memory `previous` is None even though the source was
                # genuinely offline before the restart — the persisted
                # `alerted_offline` flag is what lets us recognize this as
                # a real recovery instead of the silent startup transition.
                self._alerted_offline.discard(source)
                self._persist_alerted_offline()
                self._fire_alert(source, offline=False)

    def _persist_alerted_offline(self) -> None:
        self._store_data["alerted_offline"] = sorted(self._alerted_offline)
        self.hass.async_create_task(self._store.async_save(self._store_data))

    def _fire_alert(self, source: str, offline: bool) -> None:
        name = SOURCE_NAMES.get(source, source)
        texts = get_texts(self.hass)
        self.hass.bus.async_fire(
            f"{DOMAIN}_source_{'offline' if offline else 'online'}",
            {"source": source, "name": name},
        )
        if not self.notify_on_disconnect:
            return
        if offline:
            self._notify(
                f"{DOMAIN}_{source}_offline",
                texts["offline"].format(name=name),
            )
        else:
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "persistent_notification",
                    "dismiss",
                    {"notification_id": f"{DOMAIN}_{source}_offline"},
                )
            )
            self._notify(
                f"{DOMAIN}_{source}_online",
                texts["online"].format(name=name),
            )
