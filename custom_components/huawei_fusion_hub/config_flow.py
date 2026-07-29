"""Config flow for Huawei Fusion Hub."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    ALL_SOURCES,
    CONF_AGGREGATE_CONTROLS,
    CONF_BATTERY_CAPACITY,
    CONF_DERIVED_SENSORS,
    CONF_NOTIFY_ON_DISCONNECT,
    CONF_OVERRIDES,
    CONF_PRIORITY,
    CONF_RESERVE_SOC,
    CONF_SOURCES,
    DEFAULT_AGGREGATE_CONTROLS,
    DEFAULT_BATTERY_CAPACITY,
    DEFAULT_DERIVED_SENSORS,
    DEFAULT_NOTIFY_ON_DISCONNECT,
    DEFAULT_RESERVE_SOC,
    DOMAIN,
    SOURCE_NAMES,
)


def _derived_schema(
    enabled: bool, reserve: float, capacity: float
) -> vol.Schema:
    """Shared schema for the derived-sensors step of both flows."""
    return vol.Schema(
        {
            vol.Required(CONF_DERIVED_SENSORS, default=enabled): BooleanSelector(),
            vol.Required(CONF_RESERVE_SOC, default=reserve): NumberSelector(
                NumberSelectorConfig(
                    min=0, max=50, step=1, mode=NumberSelectorMode.BOX,
                    unit_of_measurement="%",
                )
            ),
            vol.Required(CONF_BATTERY_CAPACITY, default=capacity): NumberSelector(
                NumberSelectorConfig(
                    min=0, max=100, step=0.1, mode=NumberSelectorMode.BOX,
                    unit_of_measurement="kWh",
                )
            ),
        }
    )


def _installed_sources(hass) -> list[str]:
    """Sources that have at least one loaded config entry."""
    return [
        source
        for source in ALL_SOURCES
        if hass.config_entries.async_entries(source)
    ]


def _source_options(sources: list[str]) -> list[SelectOptionDict]:
    return [SelectOptionDict(value=s, label=SOURCE_NAMES[s]) for s in sources]


class HuaweiFusionHubConfigFlow(ConfigFlow, domain=DOMAIN):
    """Two steps: pick sources, then order them by priority."""

    VERSION = 1

    def __init__(self) -> None:
        self._sources: list[str] = []
        self._priority: list[str] = []
        self._controls: bool = DEFAULT_AGGREGATE_CONTROLS

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            self._sources = user_input[CONF_SOURCES]
            if not self._sources:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._user_schema(),
                    errors={"base": "no_sources"},
                )
            if len(self._sources) == 1:
                self._priority = self._sources
                return await self.async_step_controls()
            return await self.async_step_priority()

        return self.async_show_form(step_id="user", data_schema=self._user_schema())

    def _user_schema(self) -> vol.Schema:
        detected = _installed_sources(self.hass)
        return vol.Schema(
            {
                vol.Required(CONF_SOURCES, default=detected): SelectSelector(
                    SelectSelectorConfig(
                        options=_source_options(ALL_SOURCES),
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                )
            }
        )

    async def async_step_priority(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            priority = [user_input[f"priority_{i}"] for i in range(len(self._sources))]
            if len(set(priority)) != len(priority):
                return self.async_show_form(
                    step_id="priority",
                    data_schema=self._priority_schema(),
                    errors={"base": "duplicate_priority"},
                )
            self._priority = priority
            return await self.async_step_controls()

        return self.async_show_form(
            step_id="priority", data_schema=self._priority_schema()
        )

    def _priority_schema(self) -> vol.Schema:
        options = _source_options(self._sources)
        schema: dict[Any, Any] = {}
        for i, source in enumerate(self._sources):
            schema[vol.Required(f"priority_{i}", default=source)] = SelectSelector(
                SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
            )
        return vol.Schema(schema)

    async def async_step_controls(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            self._controls = user_input[CONF_AGGREGATE_CONTROLS]
            return await self.async_step_derived()
        return self.async_show_form(
            step_id="controls",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_AGGREGATE_CONTROLS,
                        default=DEFAULT_AGGREGATE_CONTROLS,
                    ): BooleanSelector()
                }
            ),
        )

    async def async_step_derived(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            return self.async_create_entry(
                title="Huawei Fusion Hub",
                data={
                    CONF_SOURCES: self._priority,
                    CONF_PRIORITY: self._priority,
                    CONF_NOTIFY_ON_DISCONNECT: DEFAULT_NOTIFY_ON_DISCONNECT,
                    CONF_AGGREGATE_CONTROLS: self._controls,
                    CONF_DERIVED_SENSORS: user_input[CONF_DERIVED_SENSORS],
                    CONF_RESERVE_SOC: user_input[CONF_RESERVE_SOC],
                    CONF_BATTERY_CAPACITY: user_input[CONF_BATTERY_CAPACITY],
                },
            )
        return self.async_show_form(
            step_id="derived",
            data_schema=_derived_schema(
                DEFAULT_DERIVED_SENSORS,
                DEFAULT_RESERVE_SOC,
                DEFAULT_BATTERY_CAPACITY,
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return HubOptionsFlow(config_entry)


class HubOptionsFlow(OptionsFlow):
    """Options: add/remove sources, re-order priority, toggle notifications."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry
        self._sources: list[str] = []
        self._priority: list[str] = []
        self._notify: bool = True
        self._controls: bool = False
        self._controls_default: bool = False

    def _current(self, key: str, default: Any) -> Any:
        return self._entry.options.get(key, self._entry.data.get(key, default))

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        # Current state
        current_sources: list[str] = self._entry.options.get(
            CONF_SOURCES, self._entry.data.get(CONF_SOURCES, [])
        )
        current_notify: bool = self._entry.options.get(
            CONF_NOTIFY_ON_DISCONNECT,
            self._entry.data.get(CONF_NOTIFY_ON_DISCONNECT, True),
        )
        current_controls: bool = self._entry.options.get(
            CONF_AGGREGATE_CONTROLS,
            self._entry.data.get(CONF_AGGREGATE_CONTROLS, False),
        )

        if user_input is not None:
            self._sources = user_input[CONF_SOURCES]
            self._notify = user_input[CONF_NOTIFY_ON_DISCONNECT]
            if not self._sources:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._init_schema(
                        current_sources, current_notify, current_controls
                    ),
                    errors={"base": "no_sources"},
                )
            if len(self._sources) == 1:
                self._priority = self._sources
                return await self.async_step_controls()
            return await self.async_step_priority()

        return self.async_show_form(
            step_id="init",
            data_schema=self._init_schema(
                current_sources, current_notify, current_controls
            ),
        )

    def _init_schema(
        self, sources: list[str], notify: bool, controls: bool
    ) -> vol.Schema:
        self._controls_default = controls
        return vol.Schema(
            {
                vol.Required(CONF_SOURCES, default=sources): SelectSelector(
                    SelectSelectorConfig(
                        options=_source_options(ALL_SOURCES),
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
                vol.Required(CONF_NOTIFY_ON_DISCONNECT, default=notify): BooleanSelector(),
            }
        )

    async def async_step_priority(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        current_priority: list[str] = self._entry.options.get(
            CONF_PRIORITY, self._entry.data.get(CONF_PRIORITY, self._sources)
        )
        # Keep previous order for sources that are still selected
        ordered = [s for s in current_priority if s in self._sources]
        ordered += [s for s in self._sources if s not in ordered]

        if user_input is not None:
            priority = [user_input[f"priority_{i}"] for i in range(len(self._sources))]
            if len(set(priority)) != len(priority):
                return self.async_show_form(
                    step_id="priority",
                    data_schema=self._priority_schema(ordered),
                    errors={"base": "duplicate_priority"},
                )
            self._priority = priority
            return await self.async_step_controls()

        return self.async_show_form(
            step_id="priority", data_schema=self._priority_schema(ordered)
        )

    def _priority_schema(self, ordered: list[str]) -> vol.Schema:
        options = _source_options(self._sources)
        schema: dict[Any, Any] = {}
        for i, source in enumerate(ordered):
            schema[vol.Required(f"priority_{i}", default=source)] = SelectSelector(
                SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
            )
        return vol.Schema(schema)

    async def async_step_controls(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            self._controls = user_input[CONF_AGGREGATE_CONTROLS]
            return await self.async_step_derived()
        return self.async_show_form(
            step_id="controls",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_AGGREGATE_CONTROLS,
                        default=self._controls_default,
                    ): BooleanSelector()
                }
            ),
        )

    async def async_step_derived(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        if user_input is not None:
            data = {
                CONF_SOURCES: self._sources,
                CONF_PRIORITY: self._priority,
                CONF_NOTIFY_ON_DISCONNECT: self._notify,
                CONF_AGGREGATE_CONTROLS: self._controls,
                CONF_DERIVED_SENSORS: user_input[CONF_DERIVED_SENSORS],
                CONF_RESERVE_SOC: user_input[CONF_RESERVE_SOC],
                CONF_BATTERY_CAPACITY: user_input[CONF_BATTERY_CAPACITY],
            }
            # options replace the whole dict: carry over keys not managed
            # by this flow, or they would be silently dropped
            overrides = self._entry.options.get(CONF_OVERRIDES)
            if overrides:
                data[CONF_OVERRIDES] = overrides
            return self.async_create_entry(title="", data=data)

        return self.async_show_form(
            step_id="derived",
            data_schema=_derived_schema(
                self._current(CONF_DERIVED_SENSORS, DEFAULT_DERIVED_SENSORS),
                self._current(CONF_RESERVE_SOC, DEFAULT_RESERVE_SOC),
                self._current(CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY),
            ),
        )
