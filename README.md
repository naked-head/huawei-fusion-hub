<p align="center">
  <img src="https://cdn.jsdelivr.net/gh/naked-head/huawei-fusion-hub@main/custom_components/huawei_fusion_hub/brand/icon@2x.png" alt="Huawei Fusion Hub" width="120">
</p>

# Huawei Fusion Hub — Home Assistant Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/naked-head/huawei-fusion-hub.svg)](https://github.com/naked-head/huawei-fusion-hub/releases)
[![Validate](https://github.com/naked-head/huawei-fusion-hub/actions/workflows/validate.yml/badge.svg)](https://github.com/naked-head/huawei-fusion-hub/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/naked-head/huawei-fusion-hub.svg)](https://github.com/naked-head/huawei-fusion-hub/blob/main/LICENSE)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=naked-head&repository=huawei-fusion-hub&category=integration)

A [Home Assistant](https://www.home-assistant.io/) integration that aggregates data from up to three Huawei solar monitoring integrations — **Huawei Solar** (local Modbus), **FusionSolar** (Kiosk/OpenAPI) and **FusionSolarPlus** — into a single, stable set of `sensor.hf_hub_*` entities with automatic priority-based failover.

> **Why this exists:** the local Modbus connection ([Huawei Solar](https://github.com/wlcrs/huawei_solar)) is the most reactive and accurate source, but occasionally drops. The cloud sources ([FusionSolar](https://github.com/tijsverkoyen/HomeAssistant-FusionSolar), [FusionSolarPlus](https://github.com/JortvanSchijndel/FusionSolarPlus)) are more resilient but slower. This hub sits in front of all three and always serves the best available value — so your automations keep running regardless of which source is up.

---

## ⚠️ Important notes

- This integration **does not communicate directly** with your inverter or any cloud service. It only reads entity states already published in Home Assistant by the source integrations — zero extra polling.
- At least one of the three source integrations must be installed and configured. The hub works with any combination of one, two or all three.
- Entity discovery is **language-independent**: matching is done on registry `unique_id` values (register names for Huawei Solar, numeric signal ids for FusionSolarPlus, sensor ids for FusionSolar), so the hub works regardless of your Home Assistant language or any renamed entities.
- Unofficial project, not affiliated with Huawei Technologies Co., Ltd.

---

## Features

- **Priority-based failover**: for every quantity, the hub uses the highest-priority source that is currently available. Priority is configurable from the UI at any time — including adding or removing sources.
- **232 canonical sensors** — the complete union of quantities from all three sources, including single-source entities. Sensors are grouped into logical devices: **Inverter**, **Battery**, **Battery Unit 1/2**, **Power Meter**, **Plant** and **EMMA**.
- **Stable entity IDs**: automations and dashboards keep working regardless of which source is active. Every hub sensor exposes `source` and `source_entity` attributes so you always know where the value is coming from.
- **Automatic unit normalization**: values are converted to canonical units (W, kWh, °C) even when sources report differently (kW vs W, Wh vs kWh).
- **Dynamic rediscovery**: when a source integration is added or re-enabled, the hub automatically discovers and creates the new hub entities — no restart needed — and notifies you with grouped counts.
- **Source availability alerts**: a `binary_sensor` per source (connectivity device class), an event on the bus (`huawei_fusion_hub_source_offline` / `_online`), and configurable persistent notifications when a source goes down or recovers.
- **Initial summary notification**: on first setup, a persistent notification reports how many entities were created, grouped per device and per source.
- **Optional control aggregation**: switch, select, number and button entities (inverter on/off, battery working mode, power setpoints, forcible charge…) can be proxied through the hub — off by default, with the rationale explained in the config flow.
- **Native entity categories**: measurements, Diagnostic (statuses, identifiers) and Configuration (control proxies) are separated in each device page, mirroring the source integrations' layout.
- **Multi-language**: UI and entity names in English and Italian.

---

## Installation

### Via HACS (recommended)

1. HACS → Integrations → ⋮ menu → **Custom repositories**
2. Add `https://github.com/naked-head/huawei-fusion-hub`, category **Integration**
3. Search for "Huawei Fusion Hub" and install
4. Restart Home Assistant

### Manual

1. Download the latest [release](https://github.com/naked-head/huawei-fusion-hub/releases/latest)
2. Copy `custom_components/huawei_fusion_hub` into `/config/custom_components/`
3. Restart Home Assistant

---

## Requirements

At least one of the following integrations must be installed and configured before adding the hub:

- [Huawei Solar](https://github.com/wlcrs/huawei_solar) — local Modbus, highest accuracy and frequency
- [FusionSolar](https://github.com/tijsverkoyen/HomeAssistant-FusionSolar) — cloud Kiosk or Northbound API
- [FusionSolarPlus](https://github.com/JortvanSchijndel/FusionSolarPlus) — cloud, direct credentials

---

## Configuration

1. **Settings → Devices & Services → Add Integration → Huawei Fusion Hub**
2. **Select sources**: installed integrations are auto-detected and pre-selected. You can select any combination.
3. **Set priority** (if more than one source): order the sources — the hub always tries the first available one.
4. **Aggregate control entities** (optional, off by default): choose whether switch, select, number and button controls should also be proxied through the hub. Controls exist only on the Modbus connection, so they gain no failover — the step explains the trade-off before you decide.

### Changing sources or priority

Open the integration's three-dot menu → **Configure** (Options) at any time to:
- **Add or remove** source integrations
- **Change the priority order**
- **Enable or disable control aggregation**
- **Toggle disconnect notifications**

No restart is needed when changing options.

---

## Migrating the Energy Dashboard

If you are switching from the source integrations to Huawei Fusion Hub in the Energy Dashboard and want to preserve your historical statistics, see **[ENERGY_MIGRATION.md](ENERGY_MIGRATION.md)** for a step-by-step guide.

This procedure renames the existing `statistic_id` entries in the Home Assistant database so the Energy Dashboard sees the hub entities as having the full history from the original source entities. It requires direct SQLite access and is intended for advanced users. If you are not comfortable working with databases from the command line, do not attempt this procedure — start fresh with the hub entities and let the Energy Dashboard build new statistics over time. In any case, the author assumes no responsibility for data loss or any other damage.

---

## Exposed entities

The hub exposes **232 canonical sensors** grouped into logical devices. The full correspondence table between hub entities and source entities is in **[ENTITY_MAP.md](ENTITY_MAP.md)**.

| Device | Entities |
|---|---|
| Inverter | 38 — active/reactive power, voltages, currents, yields, temperature, efficiency, PV strings… |
| Power Meter | 28 — active/reactive power, frequencies, grid import/export energy, per-phase measurements… |
| Battery | 14 — SoC, charge/discharge power, daily/total energy, bus voltage/current, status… |
| Battery Unit 1 | 62 — unit-level and per-pack (3 packs): voltage, power, SoC, temperatures, discharge energy… |
| Battery Unit 2 | 61 — same as Unit 1 |
| Plant | 18 — realtime power, daily/monthly/yearly/total energy, consumption, self-consumption ratios, flows… |
| EMMA | 11 — capacity control parameters (peak shaving, peak power, working mode, feed-in/mains limits, AC charge, PV priority). FusionSolarPlus-only, unverified: no EMMA hardware available for testing. |
| Controls (opt-in) | 18 — switch/select/number/button proxies: inverter on/off, working modes, power setpoints, SOC limits, forcible charge |

A hub sensor is created only when at least one configured source provides that quantity. Sensors only available from a single source have no failover but keep a stable entity name.

The FusionSolar column of the map covers both **Kiosk** mode (plant-level sensors) and **Northbound/OpenAPI** mode (per-device realtime data), so the hub takes full advantage of an OpenAPI account when available.

📋 **Full entity correspondence table: [ENTITY_MAP.md](ENTITY_MAP.md)**

---

## Battery runtime estimates

The hub derives two sensors from the battery power and state of charge it already aggregates:

| Entity | Meaning |
|---|---|
| `sensor.hf_hub_battery_estimated_time_to_full` | time until the battery reaches 100%, while charging |
| `sensor.hf_hub_battery_estimated_time_to_minimum` | time until it reaches the configured reserve, while discharging |

Only one of the two is ever available at a time, and **neither publishes anything while the battery is idle** (below 100 W) or when the arithmetic exceeds 24 hours. Just above the idle threshold a linear estimate reaches tens of hours, and a value clamped to a ceiling would look like a real reading.

They are computed from a rolling in-memory window of samples — 15 minutes on the local Modbus source, 20 minutes on cloud sources — so both stay `unknown` for the first few minutes after a restart. No extra polling and no recorder dependency.

### What the estimate assumes

Every estimate rests on one assumption: **that the current charge or discharge rate holds until the target**. A car starting to charge, an oven switching on, or a cloud passing over the array all invalidate it.

Rather than hide that, the hub measures it and publishes it alongside:

| Attribute | Meaning |
|---|---|
| `power_variation` | how much the battery power varied over the window, as a percentage of its own mean |
| `confidence` | `high`, `medium` or `low`, derived from `power_variation` and how full the sample window is |
| `samples`, `window_seconds` | how much history the estimate is based on |
| `estimation_method` | how it was computed — currently always `energy` |
| `capacity_kwh`, `capacity_factor` | the rated capacity used, and the conversion factor applied to it |
| `source` | which source integration supplied the underlying values |

`confidence: low` right after a sudden change in load is the system working, not failing: it means the window still holds the old regime and the number should not be trusted yet. It recovers within a few minutes.

### Configuring the estimates

Under *Settings → Devices & Services → Huawei Fusion Hub → Configure*:

- **Enable the estimates** — on by default. Nothing else depends on them.
- **Minimum charge level** — the SoC the discharge estimate counts down to, 5% by default. Set it to whatever your inverter actually stops at.
- **Battery capacity override** — only needed when the source does not publish a rated capacity. This is the **rated** capacity of the pack, not a figure you measured yourself: the conversion factor below is applied on top of it, so entering an observed value applies the correction twice.

### On accuracy

The state of charge is a property of the battery pack, but the power register is measured upstream of the DC conversion, so the two are not the same energy. The rated capacity is therefore scaled by a conversion factor before being divided by the current power.

That factor was calibrated on a single installation — one SUN2000 inverter with a LUNA2000 10 kWh battery — over three weeks and roughly 15000 published estimates. **It is a property of a particular inverter and battery pair, not of this integration**, and it will be wrong to some degree elsewhere. Deriving it per installation, from the battery's own energy counters, is [planned](https://github.com/naked-head/huawei-fusion-hub/issues).

On that plant, measured against the SoC rate actually observed over the following 30 minutes: 11% median error discharging and 4% charging while the power was steady, 13% and 17% across all estimates. Treat those as the reason the defaults are what they are, not as a specification for your own system — and if your own measurements disagree, that is worth an issue.

---

## Entity IDs

Every hub entity is pinned to `sensor.hf_hub_<key>`, where `<key>` is the canonical name listed in [ENTITY_MAP.md](ENTITY_MAP.md). The entity ID is set explicitly rather than derived from the friendly name, so it stays the same whatever your Home Assistant language is, whichever source is currently supplying the value, and however you rename things in the interface.

That is the point of the integration: an automation written against `sensor.hf_hub_battery_soc` keeps working when the Modbus connection drops and the value starts arriving from the cloud instead.

### The drift repair issue

Home Assistant 2026.8 made renaming entity IDs a first-class action and added **Recreate entity IDs** to the device page. That second one regenerates the ID from the area, device and entity names whenever a custom friendly name is set, which drops the `hf_hub_` prefix. Neither change is undone on restart, so without a check the drift would be completely silent — and every automation, template and dashboard card pointing at the old ID would quietly stop resolving.

The hub compares each entity ID against its unique ID at startup and raises a repair issue listing the ones that no longer match. **Renaming a hub entity is allowed** — nothing breaks inside the integration — but the repair issue exists to make sure it was your decision and not a side effect of a bulk action.

To resolve it, either rename the affected entities back to `sensor.hf_hub_<key>` (the issue lists the expected ID for each one), or leave them and update whatever refers to them. The issue clears by itself at the next restart once no entity is drifting.

Changing the **friendly name** of a hub entity is always safe: only the entity ID is checked.

---

## Automation example

Alert when the local Modbus connection drops and the hub falls back to cloud:

```yaml
automation:
  - alias: "Huawei Solar offline"
    triggers:
      - trigger: state
        entity_id: binary_sensor.hf_hub_huawei_solar_available
        to: "off"
        for: "00:02:00"
    actions:
      - action: notify.mobile_app_phone
        data:
          message: "Huawei Solar (Modbus) is offline — hub is now using cloud fallback."
```

Or use the event bus directly for more granular control:

```yaml
automation:
  - alias: "Hub source changed"
    triggers:
      - trigger: event
        event_type: huawei_fusion_hub_source_offline
    actions:
      - action: notify.mobile_app_phone
        data:
          message: "{{ trigger.event.data.name }} went offline."
```

---

## Source availability

A source is marked offline when more than 80% of its mapped entities are `unavailable` or `unknown`. This threshold avoids false positives when only a single entity is temporarily missing.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history.

---

## License

GPL-3.0-or-later — see [LICENSE](https://github.com/naked-head/huawei-fusion-hub/blob/main/LICENSE)

## Disclaimer

This is an unofficial integration and is not affiliated with, endorsed by, or supported by Huawei Technologies Co., Ltd. or any of its subsidiaries. Use at your own risk.

## Acknowledgments

Built with the assistance of [Claude](https://claude.ai) by Anthropic.
