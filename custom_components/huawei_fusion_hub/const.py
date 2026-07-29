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
CONF_DERIVED_SENSORS = "derived_sensors"
CONF_RESERVE_SOC = "reserve_soc"
CONF_BATTERY_CAPACITY = "battery_capacity"

DEFAULT_NOTIFY_ON_DISCONNECT = True
DEFAULT_AGGREGATE_CONTROLS = False
DEFAULT_STALE_TIMEOUT = 0  # 0 = disabled
DEFAULT_DERIVED_SENSORS = True
DEFAULT_RESERVE_SOC = 5.0
DEFAULT_BATTERY_CAPACITY = 0.0  # 0 = read from the inverter

# A source is considered offline when the fraction of its mapped
# entities in unavailable/unknown exceeds this threshold.
SOURCE_OFFLINE_THRESHOLD = 0.8

ATTR_SOURCE = "source"
ATTR_SOURCE_ENTITY = "source_entity"
ATTR_CANDIDATES = "candidates"
ATTR_ESTIMATION_METHOD = "estimation_method"
ATTR_SAMPLES = "samples"
ATTR_WINDOW_SECONDS = "window_seconds"
ATTR_CAPACITY = "capacity_kwh"
ATTR_RESERVE_SOC = "reserve_soc"
ATTR_POWER_VARIATION = "power_variation"
ATTR_CONFIDENCE = "confidence"

# --- Canonical keys read by the derived estimator ---
KEY_BATTERY_SOC = "battery_soc"
KEY_BATTERY_POWER = "battery_power"
KEY_BATTERY_CAPACITY = "battery_rated_capacity"

# --- Derived (calculated) sensor keys ---
KEY_TIME_TO_FULL = "battery_time_to_full"
KEY_TIME_TO_EMPTY = "battery_time_to_empty"
DERIVED_KEYS = [KEY_TIME_TO_FULL, KEY_TIME_TO_EMPTY]

# --- Hub device groups ---
DEVICE_HUB = "hub"
DEVICE_INVERTER = "inverter"
DEVICE_BATTERY = "battery"
DEVICE_BATTERY_UNIT_1 = "battery_unit_1"
DEVICE_BATTERY_UNIT_2 = "battery_unit_2"
DEVICE_METER = "meter"
DEVICE_PLANT = "plant"

DEVICE_NAMES = {
    DEVICE_HUB: "Huawei Fusion Hub",
    DEVICE_INVERTER: "Inverter (HF Hub)",
    DEVICE_BATTERY: "Battery (HF Hub)",
    DEVICE_BATTERY_UNIT_1: "Battery Unit 1 (HF Hub)",
    DEVICE_BATTERY_UNIT_2: "Battery Unit 2 (HF Hub)",
    DEVICE_METER: "Power Meter (HF Hub)",
    DEVICE_PLANT: "Plant (HF Hub)",
}

# dispatcher signal for runtime-added entities (suffix: entry_id)
SIGNAL_NEW_KEYS = f"{DOMAIN}_new_keys"

# storage for one-time flags (suffix: entry_id)
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.{{entry_id}}"
