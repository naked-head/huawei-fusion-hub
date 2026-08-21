"""Derived battery runtime estimates.

Two estimates are exposed: time to a full charge and time to the reserve
SoC while discharging. Both are computed from a rolling window of
(timestamp, power, SoC) samples kept in memory — no recorder dependency,
no extra polling.

Two estimation methods are used:

* ``energy`` — missing energy divided by current power. Reactive to power
  changes, but relies on the rated capacity being correct and on the SoC
  being linear in stored energy. The power the inverter reports is measured
  upstream of the DC/DC conversion, so the rated capacity is scaled by a
  per-direction conversion factor before the division.
* ``soc_rate`` — missing percentage divided by the observed SoC slope.
  Immune to both assumptions above, but lags behind sudden power changes
  and needs a SoC that moves often enough to measure. Currently disabled;
  see SOC_RATE_THRESHOLD.

The two are algebraically equivalent whenever the capacity is right and
the SoC is linear in energy, so ``energy`` is the default. ``soc_rate``
was meant to take over in the final stretch of a charge, where cell
balancing breaks the linearity assumption, but measurement showed it does
worse than ``energy`` there, so it is currently switched off. The code is
kept because the reasoning behind it still holds and a better trigger may
yet be found.

Every estimate rests on one assumption: that the current charge or
discharge rate holds until the target. How well that assumption held over
the window is measured and published as ``power_variation``, and reduced
to a ``confidence`` label.
"""
from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass

from .const import SOURCE_HUAWEI_SOLAR

_LOGGER = logging.getLogger(__name__)

METHOD_ENERGY = "energy"
METHOD_SOC_RATE = "soc_rate"

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"

# Minimum interval between two samples. _refresh_data runs on every state
# change of any mapped entity (hundreds of them), so sampling must be
# time-gated or the window would hold duplicates instead of history.
SAMPLE_INTERVAL = 15.0

# Rolling window length, per SoC source.
WINDOW_LOCAL = 900.0  # 15 min — Huawei Solar (Modbus)
WINDOW_CLOUD = 1200.0  # 20 min — FusionSolar / FusionSolarPlus

# Below this power the battery is idle and no estimate is published.
IDLE_POWER = 100.0

# Above this many minutes the estimate is not published at all. Just above
# IDLE_POWER the arithmetic produces values in the tens of hours, and a
# number clamped to the ceiling would be presented as if it were real:
# "unknown" is the only true statement available there.
MAX_MINUTES = 1440.0

# soc_rate takes over above this SoC. Set above 100 to disable it.
#
# Disabled after measurement. Over 13 days (141 evaluable estimates) it was
# worse than the energy method in every SoC band it covered:
#
#     SoC 95-97   soc_rate 70.0%   energy 34.6%   (median |relative error|)
#     SoC 97-99   soc_rate 81.1%   energy 53.3%
#     SoC 99-100  soc_rate 93.3%   energy 66.7%
#
# and it underestimated by 80% on average. The cause is that the SoC slope
# measured over the window is still the one from normal charging, while the
# battery enters absorption immediately afterwards: the past slope does not
# predict the future one precisely where the regime changes, which is the
# only place this branch is used. A slope measured over a longer window, or
# a floor on the last percent, would need validating before re-enabling.
SOC_RATE_THRESHOLD = 101.0

# Guards against reading a slope out of quantization noise: a source that
# publishes an integer SoC moves in steps, and two steps in a window are
# not a trend.
MIN_SAMPLES = 4
MIN_DISTINCT_SOC = 3
MIN_SOC_SPAN = 1.0
MIN_SLOPE = 0.005  # %/min

# Confidence cuts. The underlying measure — how much the power varied over
# the window, relative to its own mean — is measured; where the cuts fall
# was a judgement call, now tuned against 20 days of data.
#
# The error is not monotonic in the variation: the 0.10-0.15 band actually
# does better than 0.05-0.10, so cutting finer buys nothing. Over 13 days
# (10071 estimates), median |relative error| and the ratio between adjacent
# classes:
#
#     CV_HIGH   share high   error high   high/medium separation
#     0.05         42.9%        11.1%              1.43x
#     0.10         60.6%        11.9%              1.36x
#     0.20         82.9%        12.5%              2.59x
#
# 0.20 keeps 83% of estimates in `high` at 12.5% error while separating the
# classes best; tightening to 0.05 costs 40% of the coverage to gain 1.4
# points and makes the classes overlap more.
MIN_VARIATION_SAMPLES = 3
CV_HIGH = 0.20
CV_MEDIUM = 0.40
FILL_HIGH = 0.8
FILL_MEDIUM = 0.4

# Rated capacity is normalized to kWh by the coordinator, but a source
# reporting no unit at all falls through unconverted. No residential
# battery is 200 kWh, so a value above that is Wh.
CAPACITY_WH_THRESHOLD = 200.0

# The SoC is a property of the pack; the power register is measured upstream
# of the conversion. Discharging therefore delivers less energy than the
# pack loses, so the rated capacity is scaled before it is divided by that
# power. This is a conversion factor, not a capacity correction: the pack's
# own daily counters read 9.62 kWh per 100% SoC charging and 9.47
# discharging — the same within 1.6% — while the same runs measured at the
# power register read 10.35 and 8.17.
#
# Discharge: 0.897 minimises both bias and error over 13 days of published
# estimates (6961 samples). Reconstructing what the same estimates would
# have said without it gives +9.5% bias and 12.6% median error, against
# -1.8% and 11.4% with it.
#
# Charge: left at 1.0 despite the physics pointing at 1.036. On 517 clean
# windows the measured factor gives +2.6% bias where 1.0 gives -1.0%, at
# identical median error. Charging power is almost always PV on a ramp, and
# the window error there is larger than the conversion loss and has the
# opposite sign; correcting only one of the two makes the total worse.
#
# Both are properties of this inverter, not of the integration. See the
# open issue on deriving them at runtime from the battery's own counters.
CAPACITY_FACTOR_CHARGE = 1.0
CAPACITY_FACTOR_DISCHARGE = 0.897


@dataclass(frozen=True)
class RuntimeEstimate:
    """Result of one estimation pass."""

    time_to_full: float | None = None
    time_to_minimum: float | None = None
    method: str | None = None
    samples: int = 0
    window_seconds: int = 0
    source: str | None = None
    capacity: float | None = None
    capacity_factor: float | None = None
    power_variation: float | None = None
    confidence: str | None = None

    @property
    def available(self) -> bool:
        return self.time_to_full is not None or self.time_to_minimum is not None


def _slope(samples: list[tuple[float, float, float]]) -> float | None:
    """Least-squares SoC slope in %/min, or None if not measurable."""
    count = len(samples)
    if count < MIN_SAMPLES:
        return None

    socs = [s for _, _, s in samples]
    if len(set(socs)) < MIN_DISTINCT_SOC:
        return None
    if max(socs) - min(socs) < MIN_SOC_SPAN:
        return None

    origin = samples[0][0]
    times = [(t - origin) / 60 for t, _, _ in samples]
    mean_t = sum(times) / count
    mean_s = sum(socs) / count
    denominator = sum((t - mean_t) ** 2 for t in times)
    if denominator <= 0:
        return None
    numerator = sum(
        (t - mean_t) * (s - mean_s) for t, s in zip(times, socs, strict=True)
    )
    return numerator / denominator


def _variation(samples: list[tuple[float, float, float]]) -> float | None:
    """Coefficient of variation of the power over the window, as a fraction.

    This is the assumption the whole estimate rests on, measured: a value
    near zero means the rate held steady, a large value means it did not.
    """
    powers = [p for _, p, _ in samples]
    count = len(powers)
    if count < MIN_VARIATION_SAMPLES:
        return None
    mean = sum(powers) / count
    if abs(mean) < 1:
        return None
    variance = sum((p - mean) ** 2 for p in powers) / (count - 1)
    return variance**0.5 / abs(mean)


def _fill(samples: list[tuple[float, float, float]], window: float) -> float:
    """Fraction of the window actually covered by samples."""
    if len(samples) < 2 or window <= 0:
        return 0.0
    return min((samples[-1][0] - samples[0][0]) / window, 1.0)


def _confidence(variation: float | None, fill: float) -> str:
    if variation is None:
        return CONFIDENCE_LOW
    if fill >= FILL_HIGH and variation <= CV_HIGH:
        return CONFIDENCE_HIGH
    if fill >= FILL_MEDIUM and variation <= CV_MEDIUM:
        return CONFIDENCE_MEDIUM
    return CONFIDENCE_LOW


def _energy_minutes(capacity: float, delta_percent: float, power: float) -> float:
    """Minutes to move the SoC by delta_percent at the given power."""
    kwh = capacity * delta_percent / 100
    return kwh / (power / 1000) * 60


def _publishable(minutes: float) -> float | None:
    """Round an estimate, or drop it when it exceeds the ceiling."""
    if minutes > MAX_MINUTES:
        return None
    return round(minutes)


class BatteryRuntimeEstimator:
    """Rolling-window estimator fed by the coordinator on every refresh."""

    def __init__(self, reserve_soc: float, capacity_override: float | None) -> None:
        self.reserve_soc = reserve_soc
        self.capacity_override = capacity_override or None
        self._samples: deque[tuple[float, float, float]] = deque()
        self._last_sample: float | None = None
        self._result = RuntimeEstimate()

    @property
    def result(self) -> RuntimeEstimate:
        return self._result

    def reset(self) -> None:
        self._samples.clear()
        self._last_sample = None
        self._result = RuntimeEstimate()

    def update(
        self,
        now: float,
        power: float | None,
        soc: float | None,
        capacity: float | None,
        source: str | None,
    ) -> None:
        """Take a sample if the interval elapsed, then recompute."""
        if power is None or soc is None:
            self.reset()
            return
        if self._last_sample is not None and now - self._last_sample < SAMPLE_INTERVAL:
            return

        self._last_sample = now
        self._samples.append((now, power, soc))

        window = WINDOW_LOCAL if source == SOURCE_HUAWEI_SOLAR else WINDOW_CLOUD
        while self._samples and now - self._samples[0][0] > window:
            self._samples.popleft()

        self._result = self._compute(capacity, source, window)

    def _compute(
        self, capacity: float | None, source: str | None, window: float
    ) -> RuntimeEstimate:
        samples = list(self._samples)
        soc = samples[-1][2]
        power = sum(p for _, p, _ in samples) / len(samples)
        variation = _variation(samples)

        common = {
            "samples": len(samples),
            "window_seconds": int(window),
            "source": source,
            "power_variation": (
                None if variation is None else round(variation * 100, 1)
            ),
            "confidence": _confidence(variation, _fill(samples, window)),
        }

        # The override fills the same slot as the inverter's own reading: it
        # is the *rated* capacity of the pack, and the conversion factors are
        # applied on top of it. Filling it with a figure observed at the power
        # register would apply the correction twice.
        capacity = self.capacity_override or capacity
        if not capacity or capacity <= 0:
            return RuntimeEstimate(**common)
        if capacity > CAPACITY_WH_THRESHOLD:
            capacity = capacity / 1000
        # published as-is: the attribute reports the rated capacity of the
        # pack, not the conversion-scaled figure used in the arithmetic
        common["capacity"] = round(capacity, 2)

        if power > IDLE_POWER:
            common["capacity_factor"] = CAPACITY_FACTOR_CHARGE
            return self._charging(common, samples, soc, power, capacity, source)
        if power < -IDLE_POWER:
            common["capacity_factor"] = CAPACITY_FACTOR_DISCHARGE
            return self._discharging(common, soc, abs(power), capacity)
        return RuntimeEstimate(**common)

    def _charging(
        self,
        common: dict,
        samples: list[tuple[float, float, float]],
        soc: float,
        power: float,
        capacity: float,
        source: str | None,
    ) -> RuntimeEstimate:
        if soc >= 100:
            return RuntimeEstimate(
                time_to_full=0.0, method=METHOD_ENERGY, **common
            )

        minutes = _energy_minutes(
            capacity * CAPACITY_FACTOR_CHARGE, 100 - soc, power
        )
        method = METHOD_ENERGY

        if soc >= SOC_RATE_THRESHOLD and source == SOURCE_HUAWEI_SOLAR:
            slope = _slope(samples)
            if slope is not None and slope > MIN_SLOPE:
                minutes = (100 - soc) / slope
                method = METHOD_SOC_RATE

        value = _publishable(minutes)
        if value is None:
            return RuntimeEstimate(**common)
        return RuntimeEstimate(time_to_full=value, method=method, **common)

    def _discharging(
        self, common: dict, soc: float, power: float, capacity: float
    ) -> RuntimeEstimate:
        if soc <= self.reserve_soc:
            return RuntimeEstimate(
                time_to_minimum=0.0, method=METHOD_ENERGY, **common
            )

        value = _publishable(
            _energy_minutes(
                capacity * CAPACITY_FACTOR_DISCHARGE,
                soc - self.reserve_soc,
                power,
            )
        )
        if value is None:
            return RuntimeEstimate(**common)
        return RuntimeEstimate(time_to_minimum=value, method=METHOD_ENERGY, **common)
