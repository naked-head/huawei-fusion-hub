# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Links to other files in the repository are absolute, so they work in the README rendered by HACS. Relative targets are blanked by Home Assistant's markdown sanitiser, which left the links dead exactly where users read the page.

## [0.9.4] - 2026-08-29

Follow-up to the HACS default listing. No functional change to the integration itself.

### Changed

- The README now documents installation from the HACS catalogue instead of walking through adding a custom repository, and the badge says Default.

## [0.9.3] - 2026-08-28

Housekeeping release cut in response to the HACS default repository review. No functional change to the integration itself.

### Added

- README sections for the battery runtime estimates and for how hub entity IDs are assigned. The derived-sensors notification and the entity ID drift repair issue both linked to anchors that did not exist, so following either one landed the reader at the top of the document with nothing to indicate where to look.

### Changed

- Relicensed from MIT to GPL-3.0-or-later. The change reached `main` before 0.9.2 was tagged but not the tag itself, so that release shipped a LICENSE and a README that disagreed with each other. Versions up to and including 0.9.2 remain available under MIT.
- The release archive now carries the license text. It lived in the repository root only, and HACS unpacks nothing but the archive, so an installed copy received no license at all.
- Minimum Home Assistant version raised to 2026.3.0, the release from which in-tree `brand/` icons are served. Below it the integration declared support while showing no icon.

### Removed

- The `images/` copies of the three brand assets, byte-identical duplicates of the files under `custom_components/huawei_fusion_hub/brand/`. The README now points at those.

## [0.9.2] - 2026-08-24

### Changed

- HACS now installs from the release ZIP asset instead of the repository archive, so the download count reported by HACS reflects actual installations.

## [0.9.1] - 2026-08-21

### Added

- Diagnostics download (Settings → Devices & Services → Huawei Fusion Hub → Download diagnostics). Reports which source won each canonical key and which
  sources were in the running, the configured priority and per-source entity counts, and — when the battery runtime estimates are enabled — the values the estimator is reading together with its last result, conversion factor included. Credentials and plant identifiers are redacted; entity IDs are kept, since they are the point of the report.

## [0.9.0] - 2026-08-21

The hub gains its first derived sensors: how long until the battery is full, and how long until it reaches the reserve. Everything else in this release exists to make those two numbers trustworthy — the assumption behind each estimate is measured and published alongside it, and the estimator was calibrated against three weeks of its own output rather than against the datasheet. No configuration change is required; the estimates are on by default and can be turned off in the options.

### Added

- Battery runtime estimates (optional, on by default): `sensor.hf_hub_battery_estimated_time_to_full` and `sensor.hf_hub_battery_estimated_time_to_minimum`, computed from the aggregated battery power, SoC and rated capacity. Published as `duration` sensors in seconds, so the frontend renders them as hours and minutes rather than a raw minute count. No extra polling and no recorder dependency — samples are kept in a rolling in-memory window, so both sensors stay unknown for the first minutes after a restart.
- Estimates are not published below 100 W of battery power, nor when the arithmetic exceeds 24 hours: near the idle threshold a linear estimate reaches tens of hours, and a value clamped to a ceiling would be presented as a real reading.
- One-off persistent notification on the upgrade that adds the estimates, explaining what they are and where to turn them off. Not shown on fresh installations, where the config flow already covers it.
- Config flow step for the estimates: enable/disable, minimum charge level for the discharge target (default 5%), and a capacity override for sources that do not publish the rated capacity or for batteries whose real capacity has dropped with age. The override is the **rated** capacity of the pack: it fills the same slot as the inverter's own reading, and the conversion factor below is applied on top of it.
- Two estimation methods, reported per sensor in the `estimation_method` attribute. `energy` (missing energy over current power) is the one in use. `soc_rate` (missing percentage over the observed SoC slope) was written to take over in the final stretch of a charge, where cell balancing breaks the assumption that SoC is linear in stored energy, but measurement found it worse than `energy` in every SoC band it covered, because the slope measured over the window is still the one from normal charging while the battery enters absorption immediately afterwards. It ships disabled, with the code and its unit tests kept, so a better trigger can be tried without rewriting it.
- `power_variation` and `confidence` attributes on both estimates: the coefficient of variation of the power over the window, and a `high`/`medium`/`low` label derived from it together with how much of the window is filled. The estimate assumes the current rate holds until the target, and these say how well that assumption held.
- `capacity_factor` attribute on both estimates, reporting which conversion factor was applied to that reading. It makes a history export self-documenting across an upgrade, instead of having to be reverse-engineered from the numbers afterwards.
- Conversion factor on the discharge estimate. The SoC is a property of the battery pack, but `battery_power` is measured upstream of the conversion, so the two are not the same energy: over 30 monotonic SoC runs the pack's own daily counters read 9.62 kWh per 100% SoC charging and 9.47 discharging — the same within 1.6%, so the rated capacity is right — while the same runs measured at the power register read 10.35 and 8.17. The rated capacity is scaled by 0.897 before being divided by the current power, which removes the optimistic bias on `time_to_minimum`. The charge side is left unscaled: the physics points at 1.036, but charging power is almost always PV on a ramp, where the error from extrapolating a rising power is larger than the conversion loss and has the opposite sign, so correcting only one of the two made the total worse in measurement.
- Unit tests for the estimator (`tests/test_derived.py`), wired into the test workflow.

### Changed

- Sample window for cloud sources reduced from 45 to 20 minutes. FusionSolarPlus publishes about every 135 seconds, so 20 minutes still holds around 9 samples, comfortably above the minimum the estimator needs. The longer window cost nothing while the power was steady and a great deal right after it changed, which is when the estimate matters.
- Confidence cuts re-tuned. The error turns out not to be monotonic in the power variation — the 0.10–0.15 band does better than 0.05–0.10 — so cutting finer buys nothing. `high` now covers roughly four estimates in five, and the separation between the three classes is wider than with any tighter cut.
- Availability binary sensors renamed from "<source> available" to "<source> connection", so the name agrees with the Connected/Disconnected state the connectivity device class produces. Display name only: unique IDs and entity IDs are unchanged, and no migration is needed.

### Calibration and its limits

> **The numbers below were measured on a single installation** — a dual-PV
> plant (Fronius 2.7 kWp and Huawei 3.2 kWp) with one SUN2000 inverter and a
> LUNA2000 10 kWh battery, over 20 days in August 2026 and roughly 15000
> published estimates, against both a local Modbus source and a FusionSolarPlus
> cloud source running in parallel.
>
> **They are not a promise about your plant.** The conversion factor is a
> property of a particular inverter and battery pair; the accuracy figures also
> depend on load pattern, weather and how steady your consumption is. Treat
> them as the reason the defaults are what they are, not as a specification.
>
> If your own measurements disagree, that is useful information and worth
> opening an issue about. Deriving the factor per installation, from the
> battery's own daily counters, instead of shipping a constant is tracked in
> [#7](https://github.com/naked-head/huawei-fusion-hub/issues/7).

For reference, on that plant:

| | median absolute error | bias |
|---|---|---|
| discharge, steady power | 11.4% | −1.8% |
| charge, steady power | 4.0% | −1.0% |
| discharge, all estimates | 13.3% | +3.8% |
| charge, all estimates | 17.0% | +6.7% |

Measured against the SoC rate actually observed over the 30 minutes following each estimate. "Steady power" means the power varied by less than 10% over the
sample window and did not trend by more than 200 W over the following half hour; that is the regime the `high` confidence label is meant to identify.

## [0.8.0] - 2026-08-07

Home Assistant 2026.8 promoted entity ID renaming to a first-class action in the interface, added a user-configurable entity ID format and a **Recreate entity IDs** action on the device page. Renaming a source entity was always possible, but it is now something users will actually do — and this release makes the hub survive it. No configuration change is required.

### Fixed

- Source entities that are renamed are followed correctly again. A rename produces no new and no lost canonical key, and the rediscovery returned early on exactly that shape, before re-arming its state subscriptions. The listener kept tracking the old entity IDs, which never fire again, so the affected hub sensors froze on their last value until the next restart. This was a latent bug independent of 2026.8; renaming simply became a much more likely way to hit it.
- Renaming a source `switch`, `select`, `number` or `button` entity now triggers a rediscovery as well. The registry listener only accepted the `sensor` domain, so with `aggregate_controls` enabled a renamed control left its proxy pointing at an entity ID that no longer existed, permanently unavailable.
- Control proxies read their source mapping from the coordinator instead of caching the dictionary handed over when they were created. Every rediscovery rebuilds that mapping from scratch, so the cached copy went stale on the first change. The proxies also re-arm their state subscriptions when the mapping moves, instead of tracking the entity IDs they saw at startup.

### Added

- Rediscovery now reports losses, not just gains. Canonical keys that stopped resolving to any source, and keys that lost one source while keeping another, are logged at `WARNING`. Sources matched through the object ID fallback layer (rather than by unique ID) stop matching when a source entity is renamed, and until now that produced no output at all: the value silently degraded to a lower-priority source, or disappeared. No persistent notification is raised — an offline source is already covered by the availability alerts.
- A repair issue is raised when an entity created by this integration no longer uses the `hf_hub_*` entity ID it was assigned. Home Assistant preserves a renamed entity ID across restarts, and **Recreate entity IDs** rebuilds it from the area, device and entity names whenever a custom friendly name is set, which drops the `hf_hub_` prefix. Everything downstream — templates, automations, dashboards, long-term statistics, InfluxDB and Grafana queries — addresses the hub by those IDs, so the drift needed to be visible. The repair lists every affected entity with the ID that was expected, and clears itself once the IDs match again.
- `tests/test_rediscovery.py`, covering the rediscovery diff logic including the rename case above, wired into the test workflow.

## [0.7.0] - 2026-07-31

### Added

- Energy Dashboard migration guide ([ENERGY_MIGRATION.md](ENERGY_MIGRATION.md)) with step-by-step instructions for transferring long-term statistics from source integration entities to hub entities
- README section linking to the migration guide with disclaimer
- EMMA / Smart Assistant support for FusionSolarPlus 2.3.5 and later: 11 new sensors in a dedicated `EMMA (HF Hub)` device group, covering the capacity control parameters (peak shaving mode, peak power, backup SoC for peak shaving, grid charge cutoff SoC, allowed AC charge power, maximum mains power, maximum grid feed-in power, active power control mode, working mode, charge from AC, PV power priority). The device group is created only when an EMMA is present, so nothing changes on installations without one.
- EMMA realtime signals now feed the existing `meter_*` and `grid_*` entities (active, reactive and per-phase power, per-phase voltage and current, power factor, imported and exported energy). On an EMMA plant the Smart Assistant *is* the meter, so these gain a real failover path alongside Modbus and FusionSolar. The EMMA patterns are appended last, so a plant that already has a dedicated Power Sensor resolves exactly as before.
- **These EMMA entities are unverified.** They were derived from the FusionSolarPlus source code and could not be tested against a real EMMA installation. Reports from EMMA owners are welcome — in particular on whether all 11 configuration signals are returned for non-installer accounts and across EMMA hardware variants. FusionSolarPlus publishes the parameters read-only, so a wrong mapping can only produce a wrong reading, never a wrong write.
- The peak power entity reports the limit of the schedule period that is active now. The schedule details FusionSolarPlus attaches to its own entity (`periods`, `period_count`, `config_updated_at`) are not copied to the hub entity; read them from the FusionSolarPlus entity if you need them.
- Issue templates for bug reports and feature requests, with a "grumpy maintainer" disclaimer checkbox and a honeypot field.

### Changed

- Release workflow now flags pre-release tags (`vX.Y.Z-suffix`) as GitHub pre-releases instead of publishing every tag as a stable release, and falls back to the `[Unreleased]` changelog section when a pre-release tag has no matching version heading yet.

### Fixed

- Options flow no longer drops `overrides` when saving: keys not managed by the flow are carried over instead of being replaced.

## [0.6.2] - 2026-07-11

### Fixed

- Recovery notifications ("source is back online") are now correctly sent even when Home Assistant is restarted while a source is still offline: the offline flag is persisted to storage instead of living only in memory, so a genuine recovery after a restart is no longer mistaken for the silent startup transition. Previously, restarting Home Assistant while a source (e.g. Huawei Solar/Modbus) was down would suppress the eventual "back online" notification.

## [0.6.1] - 2026-07-09

### Fixed

- Entity IDs are now stable `sensor.hf_hub_<key>`: Home Assistant ignores `suggested_object_id` when `has_entity_name` is set and generated ids from device names (mixed `huawei_fusion_hub_*` / `inverter_hf_hub_*` schemes across versions). Entities now preset `self.entity_id` explicitly. Existing installs: rename registry entries with the provided script or re-add the integration after purging deleted entities.
- `via_device` warning: the hub device is now registered in `async_setup_entry` before platforms are forwarded.
- Recorder warnings for FusionSolarPlus daily statistics (consumption, self-consumption, feed-in) that can decrease slightly: state class changed from `total_increasing` to `total`.

## [0.6.0] - 2026-07-08

### Added

- Number and button write-through proxies (11 setpoints + stop forcible charge), completing control aggregation across all four platforms with the same opt-in philosophy.
- Localized backend notifications (discovery summary, rediscovery, source offline/online) in English and Italian, selected via the Home Assistant configured language.

### Fixed

- Spurious "source is back online" notifications after every Home Assistant restart: online alerts now fire only when a genuine offline alert was raised earlier in the same runtime. The startup transition (sources loading slower than the hub) is silent.

## [0.5.0] - 2026-07-08

### Added

- Optional aggregation of switch and select control entities (inverter on/off, battery working mode, charge from grid, excess PV use in TOU, capacity control mode, MPPT multimodal scanning) as write-through proxies. Off by default; a dedicated config-flow step explains why duplication is discouraged before letting the user opt in. Available in both initial setup and options.
- Entity categories: statuses, identifiers and configuration mirrors are now Diagnostic; control proxies are Configuration — matching the source integrations' device page layout.
- Complete FusionSolar coverage in the mapping: 58 sensors now match FusionSolar Northbound/OpenAPI realtime device data (Residential/String inverter, Battery, Power Sensor, Grid meter) in addition to the Kiosk plant sensors.
- Full localized names for all 221 sensors including the 90 battery pack entities (EN + IT), fixing duplicate labels in Battery Unit device pages.

### Changed

- Device model matching now uses prefix comparison, required for FusionSolar residential inverters whose model string includes the inverter type.
- ENTITY_MAP.md regenerated: complete FusionSolar column (Kiosk + OpenAPI) and new Controls section.

## [0.4.0] - 2026-07-07

### Added

- Options flow now allows adding or removing source integrations at any time, not just changing priority order.
- Entity names are now fully localized via `translation_key`: English and Italian translations included for all 131 named sensors and binary sensors.
- `icon@2x.png` (512×512) added to the `brand/` directory for correct display in HA device pages.

### Changed

- `brand/` directory renamed from `brands/` to match HACS specification.
- README rewritten following the ha-ilmeteo template: badges, feature list, installation, configuration, automation examples.
- Options flow priority step now preserves the previous order for unchanged sources when sources are added or removed.

## [0.3.0] - 2026-07-07

### Added

- Full entity coverage: 221 canonical sensors covering the complete union of the three sources, including single-source entities (inverter phase B/C, line voltages, DC input energy, hourly yield; meter three-phase and alternative meter models; battery system max power; battery units 1-2 with per-pack detail matching FSP Modules 1-2; full plant statistics, income and flows). See ENTITY_MAP.md.
- Battery Unit 1 and Battery Unit 2 sub-devices (huawei_solar battery units ↔ FusionSolarPlus Modules).
- Initial discovery summary notification: on first setup the hub reports how many entities were created, grouped per device and per source.
- Automatic rediscovery: when a source integration is installed or re-added later, the hub detects the new registry entities (debounced), creates the missing hub entities at runtime and notifies the user with grouped counts; existing entities gaining an additional fallback source are reported too.
- Online notification when a source comes back (the offline one is dismissed automatically).

### Changed

- mapping.py is now generated programmatically from structured tables instead of a hand-written list.
- Release tags use the `v` prefix from v0.3.0 onward.

## [0.2.0] - 2026-07-07

### Added

- Logical sub-devices: hub sensors are now grouped into Inverter, Battery, Power Meter and Plant devices, linked to the main hub device via `via_device`.
- Language-independent entity discovery: matching is now based on registry unique_ids (huawei_solar register names, FusionSolarPlus numeric signal ids with device-model disambiguation, FusionSolar sensor ids), with object_id fallback for older source versions.
- Device class agreement check between canonical definition and source entity to prevent false matches.

### Changed

- FusionSolarPlus matching uses `Model:pattern` syntax to disambiguate signal ids reused across device types (e.g. 10004 is meter active power and battery charge/discharge power).

## [0.1.0] - 2026-07-06

### Added

- Initial release.
- Priority-based aggregation of Huawei Solar (Modbus), FusionSolar (Kiosk/OpenAPI) and FusionSolarPlus entities.
- 15 canonical sensors covering inverter, meter and battery quantities with automatic unit normalization.
- Per-source connectivity binary sensors.
- Offline/online events on the HA event bus and optional persistent notifications.
- UI config flow with auto-detection of installed sources and configurable priority.
- Options flow to change priority and alert behavior without restart.
- English and Italian translations.

[Unreleased]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.9.4...HEAD
[0.9.4]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.9.3...v0.9.4
[0.9.3]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/naked-head/huawei-fusion-hub/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/naked-head/huawei-fusion-hub/releases/tag/v0.1.0
