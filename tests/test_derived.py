"""Unit tests for BatteryRuntimeEstimator (battery runtime estimates)."""
import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "custom_components")
)

from huawei_fusion_hub.const import SOURCE_FUSION_SOLAR_PLUS, SOURCE_HUAWEI_SOLAR
from huawei_fusion_hub.derived import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    METHOD_ENERGY,
    METHOD_SOC_RATE,
    SAMPLE_INTERVAL,
    WINDOW_CLOUD,
    WINDOW_LOCAL,
    BatteryRuntimeEstimator,
)

CAPACITY = 10.0


def _feed(estimator, series, source=SOURCE_HUAWEI_SOLAR, capacity=CAPACITY):
    """Feed (offset_seconds, power, soc) tuples, respecting the sample gate."""
    for offset, power, soc in series:
        estimator.update(offset, power, soc, capacity, source)
    return estimator.result


def test_idle_battery_publishes_nothing():
    estimator = BatteryRuntimeEstimator(5.0, None)
    result = _feed(estimator, [(0, 20, 60), (SAMPLE_INTERVAL, 20, 60)])
    assert result.time_to_full is None
    assert result.time_to_minimum is None


def test_charging_energy_method():
    # 10 kWh scaled by CAPACITY_FACTOR_CHARGE = 10.36 kWh per 100% SoC;
    # 50% missing = 5.18 kWh at 2500 W -> 124 minutes
    estimator = BatteryRuntimeEstimator(5.0, None)
    result = _feed(estimator, [(0, 2500, 50), (SAMPLE_INTERVAL, 2500, 50)])
    assert result.method == METHOD_ENERGY
    assert result.time_to_full == 124
    assert result.time_to_minimum is None


def test_discharging_stops_at_reserve():
    # 10 kWh scaled by CAPACITY_FACTOR_DISCHARGE = 8.97 kWh per 100% SoC;
    # from 55% down to the 5% reserve = 4.485 kWh at 1000 W -> 269 minutes
    estimator = BatteryRuntimeEstimator(5.0, None)
    result = _feed(estimator, [(0, -1000, 55), (SAMPLE_INTERVAL, -1000, 55)])
    assert result.time_to_minimum == 269
    assert result.time_to_full is None


def test_discharge_below_reserve_is_zero():
    estimator = BatteryRuntimeEstimator(5.0, None)
    result = _feed(estimator, [(0, -1000, 4), (SAMPLE_INTERVAL, -1000, 4)])
    assert result.time_to_minimum == 0


def test_full_battery_is_zero():
    estimator = BatteryRuntimeEstimator(5.0, None)
    result = _feed(estimator, [(0, 500, 100), (SAMPLE_INTERVAL, 500, 100)])
    assert result.time_to_full == 0


def test_estimate_above_ceiling_is_not_published():
    # 95% missing at 110 W is well over 24 hours: a clamped number would be
    # presented as real, so nothing is published at all
    estimator = BatteryRuntimeEstimator(5.0, None)
    result = _feed(estimator, [(0, 110, 5), (SAMPLE_INTERVAL, 110, 5)])
    assert result.time_to_full is None
    assert result.method is None


def test_discharge_above_ceiling_is_not_published():
    # the 108 W real-world case: 45% down to reserve would be ~42 hours
    estimator = BatteryRuntimeEstimator(5.0, None)
    result = _feed(estimator, [(0, -108, 50), (SAMPLE_INTERVAL, -108, 50)])
    assert result.time_to_minimum is None


def test_confidence_high_on_steady_power():
    estimator = BatteryRuntimeEstimator(5.0, None)
    series = [(i * 60.0, -1000 + (i % 2) * 10, 55) for i in range(16)]
    result = _feed(estimator, series)
    assert result.confidence == CONFIDENCE_HIGH
    assert result.power_variation < 1.0


def test_confidence_low_on_erratic_power():
    # oven and heat pump cycling: same mean, unusable as a prediction
    estimator = BatteryRuntimeEstimator(5.0, None)
    series = [(i * 60.0, -300 if i % 2 else -2500, 55) for i in range(16)]
    result = _feed(estimator, series)
    assert result.confidence == CONFIDENCE_LOW
    assert result.power_variation > 40


def test_confidence_low_while_window_fills():
    # steady power, but only two minutes of history after a restart
    estimator = BatteryRuntimeEstimator(5.0, None)
    series = [(i * 60.0, -1000, 55) for i in range(3)]
    result = _feed(estimator, series)
    assert result.confidence == CONFIDENCE_LOW


def test_confidence_medium_on_partial_window():
    estimator = BatteryRuntimeEstimator(5.0, None)
    series = [(i * 60.0, -1000 - (i % 3) * 200, 55) for i in range(9)]
    result = _feed(estimator, series)
    assert result.confidence == CONFIDENCE_MEDIUM


def test_variation_needs_three_samples():
    estimator = BatteryRuntimeEstimator(5.0, None)
    result = _feed(estimator, [(0, -1000, 55), (SAMPLE_INTERVAL, -1000, 55)])
    assert result.power_variation is None
    assert result.confidence == CONFIDENCE_LOW


def test_soc_rate_takes_over_in_final_stretch():
    # SoC crawling 0.1 %/min above 95%: soc_rate must win over energy,
    # which would still trust the nominal capacity
    estimator = BatteryRuntimeEstimator(5.0, None)
    series = [(i * 60.0, 400, 96.0 + i * 0.1) for i in range(11)]
    result = _feed(estimator, series)
    assert result.method == METHOD_SOC_RATE
    # 3 points missing at 0.1 %/min -> about 30 minutes
    assert 25 <= result.time_to_full <= 35


def test_soc_rate_not_used_below_threshold():
    estimator = BatteryRuntimeEstimator(5.0, None)
    series = [(i * 60.0, 2500, 80.0 + i * 0.4) for i in range(11)]
    result = _feed(estimator, series)
    assert result.method == METHOD_ENERGY


def test_soc_rate_ignored_on_cloud_source():
    estimator = BatteryRuntimeEstimator(5.0, None)
    series = [(i * 60.0, 400, 96.0 + i * 0.1) for i in range(11)]
    result = _feed(estimator, series, source=SOURCE_FUSION_SOLAR_PLUS)
    assert result.method == METHOD_ENERGY
    assert result.window_seconds == WINDOW_CLOUD


def test_soc_rate_ignored_when_soc_is_flat():
    # quantized SoC that never moves: no measurable slope, stay on energy
    estimator = BatteryRuntimeEstimator(5.0, None)
    series = [(i * 60.0, 400, 97.0) for i in range(11)]
    result = _feed(estimator, series)
    assert result.method == METHOD_ENERGY


def test_sample_gate_drops_bursts():
    estimator = BatteryRuntimeEstimator(5.0, None)
    # ten updates within a second: only the first is sampled
    result = _feed(estimator, [(i * 0.1, 2500, 50) for i in range(10)])
    assert result.samples == 1


def test_window_is_pruned():
    estimator = BatteryRuntimeEstimator(5.0, None)
    series = [(i * 60.0, 2500, 50) for i in range(30)]
    result = _feed(estimator, series)
    assert result.window_seconds == WINDOW_LOCAL
    assert result.samples <= WINDOW_LOCAL / 60 + 1


def test_capacity_override_wins():
    estimator = BatteryRuntimeEstimator(5.0, 5.0)
    # 5 kWh instead of 10: half the time (62 rather than 124)
    result = _feed(estimator, [(0, 2500, 50), (SAMPLE_INTERVAL, 2500, 50)])
    assert result.capacity == 5.0
    assert result.time_to_full == 62


def test_capacity_in_wh_is_normalized():
    estimator = BatteryRuntimeEstimator(5.0, None)
    result = _feed(
        estimator, [(0, 2500, 50), (SAMPLE_INTERVAL, 2500, 50)], capacity=10000.0
    )
    assert result.capacity == 10.0
    assert result.time_to_full == 124


def test_missing_capacity_publishes_nothing():
    estimator = BatteryRuntimeEstimator(5.0, None)
    result = _feed(
        estimator, [(0, 2500, 50), (SAMPLE_INTERVAL, 2500, 50)], capacity=None
    )
    assert result.time_to_full is None


def test_missing_soc_resets_the_buffer():
    estimator = BatteryRuntimeEstimator(5.0, None)
    _feed(estimator, [(i * 60.0, 2500, 50) for i in range(5)])
    estimator.update(400.0, 2500, None, CAPACITY, SOURCE_HUAWEI_SOLAR)
    assert estimator.result.samples == 0
    assert estimator.result.time_to_full is None


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    sys.exit(1 if failed else 0)
