"""Derived battery runtime estimates.

Two estimates are exposed: time to a full charge and time to the reserve
SoC while discharging. Both are computed from a rolling window of
(timestamp, power, SoC) samples kept in memory — no recorder dependency,
no extra polling.

Two estimation methods are used:

* ``energy`` — missing energy divided by current power. Reactive to power
  changes, but relies on the rated capacity being correct and on the SoC
  being linear in stored energy.
* ``soc_rate`` — missing percentage divided by the observed SoC slope.
  Immune to both assumptions above, but lags behind sudden power changes
  and needs a SoC that moves often enough to measure.

The two are algebraically equivalent whenever the capacity is right and
the SoC is linear in energy, so ``energy`` is the default. ``soc_rate``
takes over only in the final stretch of a charge, where cell balancing
breaks the linearity assumption, and only when the SoC comes from the
local Modbus source (cloud sources are too slow and too coarse to
differentiate).

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
WINDOW_CLOUD = 2700.0  # 45 min — FusionSolar / FusionSolarPlus

# Below this power the battery is idle and no estimate is published.
IDLE_POWER = 100.0

# Above this many minutes the estimate is not published at all. Just above
# IDLE_POWER the arithmetic produces values in the tens of hours, and a
# number clamped to the ceiling would be presented as if it were real:
# "unknown" is the only true statement available there.
MAX_MINUTES = 1440.0

# soc_rate takes over above this SoC, where cell balancing makes the
# energy model structurally wrong.
SOC_RATE_THRESHOLD = 95.0

# Guards against reading a slope out of quantization noise: a source that
# publishes an integer SoC moves in steps, and two steps in a window are
# not a trend.
MIN_SAMPLES = 4
MIN_DISTINCT_SOC = 3
MIN_SOC_SPAN = 1.0
MIN_SLOPE = 0.005  # %/min

# Confidence cuts. The underlying measure — how much the power varied over
# the window, relative to its own mean — is measured; where the cuts fall
# is a judgement call, to be re-tuned against real data.
MIN_VARIATION_SAMPLES = 3
CV_HIGH = 0.15
CV_MEDIUM = 0.40
FILL_HIGH = 0.8
FILL_MEDIUM = 0.4

# Rated capacity is normalized to kWh by the coordinator, but a source
# reporting no unit at all falls through unconverted. No residential
# battery is 200 kWh, so a value above that is Wh.
CAPACITY_WH_THRESHOLD = 200.0


@dataclass(frozen=True)
class RuntimeEstimate:
    """Result of one estimation pass."""

    time_to_full: float | None = None
    time_to_empty: float | None = None
    method: str | None = None
    samples: int = 0
    window_seconds: int = 0
    source: str | None = None
    capacity: float | None = None
    power_variation: float | None = None
    confidence: str | None = None

    @property
    def available(self) -> bool:
        return self.time_to_full is not None or self.time_to_empty is not None


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

        capacity = self.capacity_override or capacity
        if not capacity or capacity <= 0:
            return RuntimeEstimate(**common)
        if capacity > CAPACITY_WH_THRESHOLD:
            capacity = capacity / 1000
        common["capacity"] = round(capacity, 2)

        if power > IDLE_POWER:
            return self._charging(common, samples, soc, power, capacity, source)
        if power < -IDLE_POWER:
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

        minutes = _energy_minutes(capacity, 100 - soc, power)
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
                time_to_empty=0.0, method=METHOD_ENERGY, **common
            )

        value = _publishable(
            _energy_minutes(capacity, soc - self.reserve_soc, power)
        )
        if value is None:
            return RuntimeEstimate(**common)
        return RuntimeEstimate(time_to_empty=value, method=METHOD_ENERGY, **common)
