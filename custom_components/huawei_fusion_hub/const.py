"""Constants for Huawei Fusion Hub."""

DOMAIN = "huawei_fusion_hub"
ENTITY_PREFIX = "hf_hub"

# --- Source integrations ---
SOURCE_HUAWEI_SOLAR = "huawei_solar"
SOURCE_FUSION_SOLAR = "fusion_solar"
SOURCE_FUSION_SOLAR_PLUS = "fusionsolarplus"

ALL_SOURCES = [
    SOURCE_HUAWEI_SOLAR,
    SOURCE_FUSION_SOLAR,
    SOURCE_FUSION_SOLAR_PLUS,
]

SOURCE_NAMES = {
    SOURCE_HUAWEI_SOLAR: "Huawei Solar (Modbus)",
    SOURCE_FUSION_SOLAR: "FusionSolar (Kiosk/OpenAPI)",
    SOURCE_FUSION_SOLAR_PLUS: "FusionSolarPlus",
}

# --- Config keys ---
CONF_SOURCES = "sources"
CONF_PRIORITY = "priority"
CONF_NOTIFY_ON_DISCONNECT = "notify_on_disconnect"
CONF_AGGREGATE_CONTROLS = "aggregate_controls"
CONF_STALE_TIMEOUT = "stale_timeout"
CONF_OVERRIDES = "overrides"

DEFAULT_NOTIFY_ON_DISCONNECT = True
DEFAULT_AGGREGATE_CONTROLS = False
DEFAULT_STALE_TIMEOUT = 0  # 0 = disabled

# A source is considered offline when the fraction of its mapped
# entities in unavailable/unknown exceeds this threshold.
SOURCE_OFFLINE_THRESHOLD = 0.8

# Entity domains a control proxy can mirror. Used both when indexing the
# registry during discovery and when deciding whether a registry event is
# worth a rediscovery.
CONTROL_DOMAINS = ("switch", "select", "number", "button")

ATTR_SOURCE = "source"
ATTR_SOURCE_ENTITY = "source_entity"
ATTR_CANDIDATES = "candidates"

# --- Hub device groups ---
DEVICE_HUB = "hub"
DEVICE_INVERTER = "inverter"
DEVICE_BATTERY = "battery"
DEVICE_BATTERY_UNIT_1 = "battery_unit_1"
DEVICE_BATTERY_UNIT_2 = "battery_unit_2"
DEVICE_METER = "meter"
DEVICE_PLANT = "plant"
DEVICE_EMMA = "emma"

DEVICE_NAMES = {
    DEVICE_HUB: "Huawei Fusion Hub",
    DEVICE_INVERTER: "Inverter (HF Hub)",
    DEVICE_BATTERY: "Battery (HF Hub)",
    DEVICE_BATTERY_UNIT_1: "Battery Unit 1 (HF Hub)",
    DEVICE_BATTERY_UNIT_2: "Battery Unit 2 (HF Hub)",
    DEVICE_METER: "Power Meter (HF Hub)",
    DEVICE_PLANT: "Plant (HF Hub)",
    DEVICE_EMMA: "EMMA (HF Hub)",
}

# dispatcher signal for runtime-added entities (suffix: entry_id)
SIGNAL_NEW_KEYS = f"{DOMAIN}_new_keys"

# dispatcher signal fired when the control mapping changed, so the
# already-created control proxies re-arm their state subscriptions
# (suffix: entry_id)
SIGNAL_CONTROLS_CHANGED = f"{DOMAIN}_controls_changed"

# repair issue raised when a hub entity_id no longer matches its unique_id
ISSUE_ENTITY_ID_DRIFT = "entity_id_drift"

# storage for one-time flags (suffix: entry_id)
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.{{entry_id}}"
