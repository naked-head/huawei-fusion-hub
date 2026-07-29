"""Aggregated sensors exposed by the hub."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CANDIDATES,
    ATTR_CAPACITY,
    ATTR_CONFIDENCE,
    ATTR_ESTIMATION_METHOD,
    ATTR_POWER_VARIATION,
    ATTR_RESERVE_SOC,
    ATTR_SAMPLES,
    ATTR_SOURCE,
    ATTR_SOURCE_ENTITY,
    ATTR_WINDOW_SECONDS,
    DEVICE_BATTERY,
    DEVICE_HUB,
    DEVICE_NAMES,
    DOMAIN,
    ENTITY_PREFIX,
    KEY_TIME_TO_EMPTY,
    KEY_TIME_TO_FULL,
    SIGNAL_NEW_KEYS,
)
from .coordinator import HubCoordinator
from .mapping import SENSOR_DEFS_BY_KEY, HubSensorDef


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HubCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HubSensor(coordinator, SENSOR_DEFS_BY_KEY[key])
        for key in coordinator.candidates
    )

    derived_added = False
    if coordinator.derived_available:
        async_add_entities(_derived_entities(coordinator))
        derived_added = True

    @callback
    def _add_new_keys(new_keys: list[str]) -> None:
        nonlocal derived_added
        async_add_entities(
            HubSensor(coordinator, SENSOR_DEFS_BY_KEY[key]) for key in new_keys
        )
        # the battery source may have appeared only now (source added or
        # re-enabled at runtime), making the estimates possible
        if not derived_added and coordinator.derived_available:
            async_add_entities(_derived_entities(coordinator))
            derived_added = True

    entry.async_on_unload(
        async_dispatcher_connect(
            hass, f"{SIGNAL_NEW_KEYS}_{entry.entry_id}", _add_new_keys
        )
    )


def _derived_entities(coordinator: HubCoordinator) -> list[HubDerivedSensor]:
    return [
        HubDerivedSensor(coordinator, KEY_TIME_TO_FULL, "mdi:battery-clock"),
        HubDerivedSensor(coordinator, KEY_TIME_TO_EMPTY, "mdi:battery-clock-outline"),
    ]


class HubSensor(CoordinatorEntity[HubCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HubCoordinator, sensor_def: HubSensorDef) -> None:
        super().__init__(coordinator)
        self._def = sensor_def
        self._attr_unique_id = f"{ENTITY_PREFIX}_{sensor_def.key}"
        # has_entity_name makes HA ignore suggested_object_id and build the
        # entity_id from the device name; preset it to keep stable hf_hub_* ids
        self.entity_id = f"sensor.{ENTITY_PREFIX}_{sensor_def.key}"
        self._attr_translation_key = sensor_def.key
        self._attr_device_class = sensor_def.device_class
        self._attr_state_class = sensor_def.state_class
        self._attr_native_unit_of_measurement = sensor_def.unit
        self._attr_icon = sensor_def.icon
        self._attr_entity_category = sensor_def.category
        device = sensor_def.device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device)},
            name=DEVICE_NAMES[device],
            manufacturer="naked-head",
            model="Aggregated device",
            entry_type=DeviceEntryType.SERVICE,
            via_device=(DOMAIN, DEVICE_HUB),
        )

    @property
    def native_value(self):
        resolved = self.coordinator.data.get(self._def.key)
        return resolved.value if resolved else None

    @property
    def available(self) -> bool:
        resolved = self.coordinator.data.get(self._def.key)
        return bool(resolved and resolved.value is not None)

    @property
    def extra_state_attributes(self):
        resolved = self.coordinator.data.get(self._def.key)
        return {
            ATTR_SOURCE: resolved.source if resolved else None,
            ATTR_SOURCE_ENTITY: resolved.source_entity if resolved else None,
            ATTR_CANDIDATES: self.coordinator.candidates.get(self._def.key, {}),
        }


class HubDerivedSensor(CoordinatorEntity[HubCoordinator], SensorEntity):
    """Battery runtime estimate: calculated, not aggregated from a source."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator: HubCoordinator, key: str, icon: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{ENTITY_PREFIX}_{key}"
        self.entity_id = f"sensor.{ENTITY_PREFIX}_{key}"
        self._attr_translation_key = key
        self._attr_icon = icon
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DEVICE_BATTERY)},
            name=DEVICE_NAMES[DEVICE_BATTERY],
            manufacturer="naked-head",
            model="Aggregated device",
            entry_type=DeviceEntryType.SERVICE,
            via_device=(DOMAIN, DEVICE_HUB),
        )

    @property
    def _estimate(self):
        estimator = self.coordinator.estimator
        return estimator.result if estimator else None

    @property
    def native_value(self):
        estimate = self._estimate
        if estimate is None:
            return None
        if self._key == KEY_TIME_TO_FULL:
            return estimate.time_to_full
        return estimate.time_to_empty

    @property
    def available(self) -> bool:
        return self.native_value is not None

    @property
    def extra_state_attributes(self):
        estimate = self._estimate
        estimator = self.coordinator.estimator
        if estimate is None or estimator is None:
            return {}
        attributes = {
            ATTR_ESTIMATION_METHOD: estimate.method,
            ATTR_CONFIDENCE: estimate.confidence,
            ATTR_POWER_VARIATION: estimate.power_variation,
            ATTR_SAMPLES: estimate.samples,
            ATTR_WINDOW_SECONDS: estimate.window_seconds,
            ATTR_CAPACITY: estimate.capacity,
            ATTR_SOURCE: estimate.source,
        }
        if self._key == KEY_TIME_TO_EMPTY:
            attributes[ATTR_RESERVE_SOC] = estimator.reserve_soc
        return attributes
